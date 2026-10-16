import logging
import random
from typing import Tuple, Optional, Union

try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

from .multimodal_health_engine import BASE_GROWTH_BENCHMARKS

logger = logging.getLogger("agroguard.cv_service")

class CVService:
    """
    Computer Vision Stalk Height Measurement & Estimation Service.
    Supports:
    1. ArUco & Physical reference marker detection (OpenCV calibration)
    2. Simulated / Calibrated height measurement for testing and verification
    """

    @staticmethod
    def simulate_height_cm(
        week_key: str,
        is_stunted: bool = False
    ) -> Tuple[float, str]:
        """
        Generates realistic stalk height in cm based on the agronomic benchmark table.
        If is_stunted is True, generates height below minimum range for testing stunting.
        """
        bench = BASE_GROWTH_BENCHMARKS.get(week_key, BASE_GROWTH_BENCHMARKS["Week 1"])
        h_min = bench["height_min"]
        h_max = bench["height_max"]

        if is_stunted:
            # Produce height 30% below expected minimum (or lower)
            measured_height = max(round(h_min * 0.70, 1), 2.0)
        else:
            # Produce height within normal expected range
            measured_height = round(random.uniform(h_min + (h_max - h_min) * 0.25, h_max - (h_max - h_min) * 0.15), 1)

        return measured_height, "SIMULATED_BENCHMARK"

    @staticmethod
    def detect_height_marker_cm(
        image_path: str,
        marker_real_height_cm: float = 5.0
    ) -> Tuple[Optional[float], str]:
        """
        Analyzes image using OpenCV to detect an ArUco or colored reference marker at stalk base
        to calculate real stalk height in centimeters.
        """
        if not OPENCV_AVAILABLE:
            return None, "OPENCV_UNAVAILABLE"

        try:
            img = cv2.imread(image_path)
            if img is None:
                return None, "IMAGE_LOAD_FAILED"

            h, w, _ = img.shape
            
            # 1. Check for ArUco Marker
            try:
                aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
                aruco_params = cv2.aruco.DetectorParameters()
                detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)
                corners, ids, _ = detector.detectMarkers(img)

                if ids is not None and len(corners) > 0:
                    c = corners[0][0]
                    # Marker pixel height
                    marker_pixel_h = max(
                        np.linalg.norm(c[0] - c[3]),
                        np.linalg.norm(c[1] - c[2])
                    )
                    if marker_pixel_h > 5:
                        px_per_cm = marker_pixel_h / marker_real_height_cm
                        # Estimate plant height by finding green canopy bounding box
                        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                        green_mask = cv2.inRange(hsv, np.array([25, 30, 30]), np.array([95, 255, 255]))
                        pts = cv2.findNonZero(green_mask)
                        if pts is not None:
                            _, y, _, bh = cv2.boundingRect(pts)
                            estimated_cm = round(bh / px_per_cm, 1)
                            return estimated_cm, "ARUCO_CALIBRATED"
            except Exception as e:
                logger.debug(f"ArUco detection not triggered: {str(e)}")

            # 2. Check for Blue Calibration Base Marker
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            lower_blue = np.array([100, 100, 50])
            upper_blue = np.array([140, 255, 255])
            blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)
            
            blue_contours, _ = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if blue_contours:
                largest_c = max(blue_contours, key=cv2.contourArea)
                if cv2.contourArea(largest_c) > 50:
                    _, _, _, mh = cv2.boundingRect(largest_c)
                    px_per_cm = mh / marker_real_height_cm
                    
                    green_mask = cv2.inRange(hsv, np.array([25, 30, 30]), np.array([95, 255, 255]))
                    pts = cv2.findNonZero(green_mask)
                    if pts is not None:
                        _, _, _, ph = cv2.boundingRect(pts)
                        measured_cm = round(ph / px_per_cm, 1)
                        return measured_cm, "COLOR_MARKER_CALIBRATED"

        except Exception as e:
            logger.warning(f"Marker-based height measurement error: {str(e)}")

        return None, "NO_MARKER_DETECTED"

    @staticmethod
    def extract_foliar_visual_evidence(image_path: str) -> dict:
        """
        Visual Foliar Scouting Analyzer (Fallback):
        Extracts quantitative chromatic and morphological lesion evidence from foliar tissue.
        Uses Agronomic Excess Green Index (ExG = 2G - R - B) and Plant Canopy ROI constraint
        to ensure background soil, mulch, and gravel are NOT misclassified as foliar lesions.
        """
        defaults = {
            "rust_evidence": 0.0,
            "necrotic_area_ratio": 0.0,
            "chlorosis_ratio": 0.0,
            "green_foliage_ratio": 0.0,
            "total_affected_ratio": 0.0,
            "lesion_count": 0,
            "dominant_lesion_aspect_ratio": 1.0,
            "foliar_pixel_coverage": 0.0
        }

        if not OPENCV_AVAILABLE or not image_path:
            return defaults

        try:
            img = cv2.imread(image_path)
            if img is None:
                return defaults

            h, w, _ = img.shape
            total_img_pixels = float(h * w)
            if total_img_pixels <= 0:
                return defaults

            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            b, g, r = cv2.split(img.astype(np.float32))

            # 1. Agronomic Excess Green Index (ExG = 2G - R - B)
            # Living maize foliage strongly reflects green over red/blue
            exg = 2.0 * g - r - b

            # Living photosynthetic foliage (includes young lime-green & dark green, Hue 22 to 88)
            is_green_leaf = (exg > 12.0) & (hsv[:, :, 0] >= 22) & (hsv[:, :, 0] <= 88) & (hsv[:, :, 1] >= 30)
            green_mask = is_green_leaf.astype(np.uint8) * 255

            # Morphological opening to clean small non-plant speckles (e.g. reflections on mulch)
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            green_clean = cv2.morphologyEx(green_mask, cv2.MORPH_OPEN, kernel)

            green_pixels = float(cv2.countNonZero(green_clean))
            if green_pixels < (total_img_pixels * 0.02):
                # Extremely low foliar coverage in camera view
                return defaults

            # 2. Plant Canopy Region of Interest (ROI)
            # Dilate green foliage slightly (14px) to encompass lesion margins and leaf edges
            # Any rust or necrotic pixels OUTSIDE this canopy ROI are background soil/mulch and discarded
            canopy_roi = cv2.dilate(green_clean, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (14, 14)), iterations=1)

            # 3. Rust pustules: Cinnamon/reddish-orange (Hue 5-20, Sat >= 90, Val >= 50) inside Canopy ROI
            is_rust = (hsv[:, :, 0] >= 5) & (hsv[:, :, 0] <= 20) & (hsv[:, :, 1] >= 90) & (hsv[:, :, 2] >= 50)
            rust_mask = cv2.bitwise_and(is_rust.astype(np.uint8) * 255, canopy_roi)
            rust_pixels = float(cv2.countNonZero(rust_mask))

            # 4. Chlorosis: High brightness yellow midribs (Hue 22-33, Sat >= 90, Val >= 90, ExG < 12) inside Canopy ROI
            is_yellow = (hsv[:, :, 0] >= 22) & (hsv[:, :, 0] <= 33) & (hsv[:, :, 1] >= 90) & (hsv[:, :, 2] >= 90) & (exg < 12.0)
            yellow_mask = cv2.bitwise_and(is_yellow.astype(np.uint8) * 255, canopy_roi)
            yellow_pixels = float(cv2.countNonZero(yellow_mask))

            # 5. Necrotic desiccated tissue: low ExG (ExG <= 0), tan/gray (Sat >= 35, Val 40-185) inside Canopy ROI
            is_necrotic = (exg <= 0.0) & (hsv[:, :, 0] >= 10) & (hsv[:, :, 0] <= 28) & (hsv[:, :, 1] >= 35) & (hsv[:, :, 2] >= 40) & (hsv[:, :, 2] <= 185)
            necrotic_mask = cv2.bitwise_and(is_necrotic.astype(np.uint8) * 255, canopy_roi)
            # Subtract overlap with green leaves
            necrotic_mask = cv2.bitwise_and(necrotic_mask, cv2.bitwise_not(green_clean))
            necrotic_pixels = float(cv2.countNonZero(necrotic_mask))

            # Total true foliar surface
            total_foliar = green_pixels + necrotic_pixels + rust_pixels
            if total_foliar <= 0:
                return defaults

            rust_evidence = min(rust_pixels / total_foliar, 1.0)
            necrotic_ratio = min(necrotic_pixels / total_foliar, 1.0)
            chlorosis_ratio = min(yellow_pixels / total_foliar, 1.0)
            green_foliage_ratio = min(green_pixels / total_foliar, 1.0)
            total_affected = min(rust_evidence + necrotic_ratio + chlorosis_ratio, 1.0)

            # Morphology: analyze lesion shapes (cigar-shaped vs rectangular)
            lesion_combined = cv2.bitwise_or(necrotic_mask, rust_mask)
            contours, _ = cv2.findContours(lesion_combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            lesion_count = 0
            aspect_ratios = []
            min_lesion_area = max(total_foliar * 0.001, 15.0)

            for c in contours:
                area = cv2.contourArea(c)
                if area >= min_lesion_area:
                    lesion_count += 1
                    _, _, cw, ch = cv2.boundingRect(c)
                    ar = max(cw, ch) / (min(cw, ch) + 1e-5)
                    aspect_ratios.append(ar)

            dominant_ar = float(np.median(aspect_ratios)) if aspect_ratios else 1.0

            return {
                "rust_evidence": round(rust_evidence, 4),
                "necrotic_area_ratio": round(necrotic_ratio, 4),
                "chlorosis_ratio": round(chlorosis_ratio, 4),
                "green_foliage_ratio": round(green_foliage_ratio, 4),
                "total_affected_ratio": round(total_affected, 4),
                "lesion_count": lesion_count,
                "dominant_lesion_aspect_ratio": round(dominant_ar, 2),
                "foliar_pixel_coverage": round(total_foliar / total_img_pixels, 4)
            }

        except Exception as e:
            logger.warning(f"Error during foliar visual evidence extraction: {str(e)}")
            return defaults

