# ML Models Folder

This directory contains the machine learning weights and training scripts for AgroGuard:

### 1. Model Checkpoints
- `growth_stage_model.pt` — MobileNetV2 growth stage classification model (Weeks 1–9).
- `disease_model.pt` — MobileNetV2 foliar disease classification model (PlantVillage benchmark: Healthy, Common Rust, Northern Leaf Blight, Gray Leaf Spot).

### 2. Training Pipelines
- `train_disease_model_colab.ipynb` — Complete 1-click Google Colab notebook for training `disease_model.pt` on free GPU in ~4 minutes.
- `train_disease_model.py` — Standalone Python training script.

### 3. Automatic Detection
When `disease_model.pt` is placed in this folder, the AgroGuard backend automatically detects it on startup, switches the disease engine from OpenCV scouting fallback to `NEURAL_CLASSIFIER`, and enables deep learning foliar diagnostics.
