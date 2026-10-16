import logging
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional

from ..config import settings
from ..schemas import (
    TemporalObservationOut,
    ObservationsResponse
)
from .data_quality_service import DataQualityService

logger = logging.getLogger("agroguard.temporal_observation_service")

ADVERSE_HEALTH_STATES = {"STUNTED", "INFECTED", "STUNTED_AND_INFECTED"}
ADVERSE_HEIGHT_STATES = {"BELOW_EXPECTED"}
NORMAL_HEALTH_STATES = {"NORMAL"}
NORMAL_HEIGHT_STATES = {"WITHIN_EXPECTED"}

class TemporalObservationService:
    @staticmethod
    def generate_observation_id(
        farm_id: str,
        observation_type: str,
        affected_scan_ids: List[str]
    ) -> str:
        """
        Generates a deterministic observation ID so identical observations
        share a stable identifier across requests.
        """
        raw = f"{farm_id}:{observation_type}:{','.join(sorted(affected_scan_ids))}"
        hash_hex = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
        return f"obs_{hash_hex}"

    @classmethod
    def check_height_change(
        cls,
        prev: Dict[str, Any],
        curr: Dict[str, Any],
        tolerance_cm: float
    ) -> Optional[TemporalObservationOut]:
        prev_h = (prev.get("height") or {}).get("measured_height_cm")
        curr_h = (curr.get("height") or {}).get("measured_height_cm")

        if prev_h is None or curr_h is None:
            return None

        delta = curr_h - prev_h

        if delta < -tolerance_cm:
            affected = [str(prev.get("scan_id", "")), str(curr.get("scan_id", ""))]
            farm_id = str(curr.get("farm_id") or prev.get("farm_id", ""))
            return TemporalObservationOut(
                observation_id=cls.generate_observation_id(farm_id, "HEIGHT_DECREASE_OBSERVED", affected),
                observation_type="HEIGHT_DECREASE_OBSERVED",
                severity="WARNING",
                headline="Height decrease observed between consecutive scans",
                detail=(
                    f"Measured stalk height changed from {prev_h} cm to {curr_h} cm "
                    f"(Δ{delta:+.1f} cm, exceeds ±{tolerance_cm} cm measurement tolerance)."
                ),
                affected_scans=affected
            )
        return None

    @classmethod
    def flush_disease_streak(
        cls,
        streak: Dict[str, Any],
        farm_id: str,
        min_persistence_count: int,
        min_confidence: float
    ) -> Optional[TemporalObservationOut]:
        if streak["count"] >= min_persistence_count and streak["disease"]:
            affected = list(streak["scans"])
            disease_name = streak["disease"]
            count = streak["count"]
            obs = TemporalObservationOut(
                observation_id=cls.generate_observation_id(farm_id, "DISEASE_PERSISTENCE_OBSERVED", affected),
                observation_type="DISEASE_PERSISTENCE_OBSERVED",
                severity="WARNING",
                headline=f"{disease_name} detected across {count} consecutive scans",
                detail=(
                    f"{disease_name} confirmed (confidence ≥ {min_confidence * 100:.0f}%) "
                    f"in {count} consecutive scans."
                ),
                affected_scans=affected
            )
            streak["disease"] = None
            streak["count"] = 0
            streak["scans"] = []
            return obs
        return None

    @classmethod
    def update_disease_streak(
        cls,
        scan: Dict[str, Any],
        streak: Dict[str, Any],
        min_persistence_count: int,
        min_confidence: float,
        no_disease_labels: set
    ) -> Optional[TemporalObservationOut]:
        d_info = scan.get("disease_log") or {}
        disease = d_info.get("detected_disease")
        confidence = float(d_info.get("confidence_score", 0.0) or 0.0)
        farm_id = str(scan.get("farm_id", ""))
        scan_id = str(scan.get("scan_id", ""))

        is_confirmed = (
            disease is not None
            and disease not in no_disease_labels
            and confidence >= min_confidence
        )

        emitted = None

        if is_confirmed and disease == streak["disease"]:
            streak["count"] += 1
            streak["scans"].append(scan_id)
        elif is_confirmed:
            # Different confirmed disease: flush previous episode, start new
            emitted = cls.flush_disease_streak(streak, farm_id, min_persistence_count, min_confidence)
            streak["disease"] = disease
            streak["count"] = 1
            streak["scans"] = [scan_id]
        else:
            # Healthy or unconfirmed: flush previous episode, reset
            emitted = cls.flush_disease_streak(streak, farm_id, min_persistence_count, min_confidence)
            streak["disease"] = None
            streak["count"] = 0
            streak["scans"] = []

        return emitted

    @classmethod
    def update_recovery_state(
        cls,
        scan: Dict[str, Any],
        state: Dict[str, Any],
        min_recovery_count: int
    ) -> Optional[TemporalObservationOut]:
        health = (scan.get("health") or {}).get("growth_status", "UNKNOWN")
        height = (scan.get("height") or {}).get("height_status", "UNKNOWN")
        farm_id = str(scan.get("farm_id", ""))
        scan_id = str(scan.get("scan_id", ""))

        is_adverse = (health in ADVERSE_HEALTH_STATES) or (height in ADVERSE_HEIGHT_STATES)
        is_normal = (not is_adverse) and ((health in NORMAL_HEALTH_STATES) or (height in NORMAL_HEIGHT_STATES))

        # 1. Adverse resets the normal streak and captures the latest adverse state
        if is_adverse:
            state["prior_adverse"] = health if health in ADVERSE_HEALTH_STATES else height
            state["normal_streak"] = 0
            state["scans"] = []
            return None

        # 2. Normal after prior adverse increments recovery streak
        if is_normal and state["prior_adverse"] is not None:
            state["normal_streak"] += 1
            state["scans"].append(scan_id)

            if state["normal_streak"] >= min_recovery_count:
                prior = state["prior_adverse"]
                affected = list(state["scans"])
                obs = TemporalObservationOut(
                    observation_id=cls.generate_observation_id(farm_id, "RECOVERY_OBSERVED", affected),
                    observation_type="RECOVERY_OBSERVED",
                    severity="INFO",
                    headline="Recovery trend observed",
                    detail=(
                        f"Crop condition improved from {prior} to NORMAL across "
                        f"{state['normal_streak']} consecutive normal observations."
                    ),
                    affected_scans=affected
                )
                # Reset state so subsequent recovery episodes can be detected
                state["prior_adverse"] = None
                state["normal_streak"] = 0
                state["scans"] = []
                return obs
            return None

        # 3. Neither adverse nor normal (e.g. UNKNOWN, REJECTED)
        if not is_normal:
            state["prior_adverse"] = None
            state["normal_streak"] = 0
            state["scans"] = []

        return None

    @classmethod
    def detect_observations(
        cls,
        farm_id: str,
        scans: List[Dict[str, Any]],
        farm_sowing_date: Optional[str]
    ) -> ObservationsResponse:
        """
        Executes single-pass temporal observation detection over chronologically sorted scans.
        """
        data_quality = DataQualityService.evaluate_quality(scans, farm_sowing_date)
        tz = DataQualityService.get_timezone()
        generated_at = datetime.now(tz).isoformat()

        tolerance_cm = settings.MODULE4_HEIGHT_TOLERANCE_CM
        min_conf = settings.MODULE4_MIN_DISEASE_CONFIDENCE
        min_pers = settings.MODULE4_MIN_PERSISTENCE_COUNT
        min_rec = settings.MODULE4_MIN_RECOVERY_COUNT
        no_disease = set(
            label.strip()
            for label in settings.MODULE4_NO_DISEASE_LABELS.split(",")
            if label.strip()
        )

        observations: List[TemporalObservationOut] = []

        disease_streak: Dict[str, Any] = {"disease": None, "count": 0, "scans": []}
        recovery_state: Dict[str, Any] = {"prior_adverse": None, "normal_streak": 0, "scans": []}

        for i in range(len(scans)):
            curr = scans[i]

            # 1. Height change (pairwise consecutive)
            if i > 0:
                prev = scans[i - 1]
                h_obs = cls.check_height_change(prev, curr, tolerance_cm)
                if h_obs:
                    observations.append(h_obs)

            # 2. Disease persistence (streak advancing with episode-boundary emission)
            d_obs = cls.update_disease_streak(curr, disease_streak, min_pers, min_conf, no_disease)
            if d_obs:
                observations.append(d_obs)

            # 3. Recovery detection (normal-streak following adverse state)
            r_obs = cls.update_recovery_state(curr, recovery_state, min_rec)
            if r_obs:
                observations.append(r_obs)

        # Flush any trailing disease streak after the final scan
        trailing_d = cls.flush_disease_streak(disease_streak, farm_id, min_pers, min_conf)
        if trailing_d:
            observations.append(trailing_d)

        return ObservationsResponse(
            farm_id=farm_id,
            generated_at=generated_at,
            data_quality=data_quality,
            observations=observations
        )
