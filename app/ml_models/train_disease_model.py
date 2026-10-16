"""
AgroGuard Corn Foliar Pathology Training Script (MobileNetV2 Transfer Learning)
Dataset: PlantVillage Corn Dataset (4,188 images)
Classes:
  0: Blight -> Northern Leaf Blight (Exserohilum turcicum)
  1: Common_Rust -> Corn Common Rust (Puccinia sorghi)
  2: Gray_Leaf_Spot -> Corn Gray Leaf Spot (Cercospora zeae-maydis)
  3: Healthy -> Healthy Corn Foliage

Can be executed on Google Colab or any machine with GPU.
"""

import os
import shutil
import time
import copy
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split
from torchvision import datasets, transforms, models

def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("=" * 65)
    print(f"PyTorch Version : {torch.__version__}")
    print(f"Compute Device  : {device}")
    if torch.cuda.is_available():
        print(f"GPU Model       : {torch.cuda.get_device_name(0)}")
    else:
        print("Running on CPU.")
    print("=" * 65)

    # 1. Download Dataset via kagglehub
    try:
        import kagglehub
        print("\n[1/6] Fetching PlantVillage Corn Pathology Dataset...")
        raw_dir = kagglehub.dataset_download("smaranjitghose/corn-or-maize-leaf-disease-dataset")
        print(f"Dataset downloaded to: {raw_dir}")
    except Exception as e:
        print(f"kagglehub failed: {e}. Please ensure dataset is in ./data")
        raw_dir = "./data"

    subdirs = [d for d in os.listdir(raw_dir) if os.path.isdir(os.path.join(raw_dir, d))]
    data_dir = os.path.join(raw_dir, "data") if "data" in subdirs else raw_dir

    print("\n[2/6] Class Distributions:")
    total_imgs = 0
    for cls_name in sorted(os.listdir(data_dir)):
        cls_path = os.path.join(data_dir, cls_name)
        if os.path.isdir(cls_path):
            imgs = [f for f in os.listdir(cls_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            total_imgs += len(imgs)
            print(f"  • {cls_name:<20}: {len(imgs):>4} images")
    print(f"Total Annotated Images: {total_imgs}")

    # 2. Preprocessing & Augmentations
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.3),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.15),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    full_dataset = datasets.ImageFolder(data_dir, transform=train_transform)
    raw_classes = full_dataset.classes

    train_size = int(0.80 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    train_dataset, val_dataset_raw = random_split(
        full_dataset, [train_size, val_size], generator=torch.Generator().manual_seed(42)
    )

    val_dataset_clean = datasets.ImageFolder(data_dir, transform=val_transform)
    val_dataset = torch.utils.data.Subset(val_dataset_clean, val_dataset_raw.indices)

    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True, num_workers=2, pin_memory=True)
    val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False, num_workers=2, pin_memory=True)

    print(f"\n[3/6] Dataset Split: {len(train_dataset)} Train, {len(val_dataset)} Validation")

    # 3. Model Architecture Setup
    print("\n[4/6] Initializing MobileNetV2 with ImageNet weights...")
    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)

    for param in model.features.parameters():
        param.requires_grad = False

    num_classes = len(raw_classes)
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.2),
        nn.Linear(model.last_channel, num_classes)
    )
    model = model.to(device)

    # 4. Training Loop
    print("\n[5/6] Starting Training (5 Epochs)...")
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.classifier.parameters(), lr=1e-3, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=5)

    EPOCHS = 5
    best_val_acc = 0.0
    best_weights = copy.deepcopy(model.state_dict())
    history = {'train_loss': [], 'train_acc': [], 'val_loss': [], 'val_acc': []}

    start_time = time.time()
    for epoch in range(EPOCHS):
        model.train()
        running_loss, running_corrects = 0.0, 0
        for inputs, labels in train_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            _, preds = torch.max(outputs, 1)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * inputs.size(0)
            running_corrects += torch.sum(preds == labels.data)

        train_loss = running_loss / len(train_dataset)
        train_acc = (running_corrects.double() / len(train_dataset)).item() * 100

        model.eval()
        val_loss, val_corrects = 0.0, 0
        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                loss = criterion(outputs, labels)
                _, preds = torch.max(outputs, 1)
                val_loss += loss.item() * inputs.size(0)
                val_corrects += torch.sum(preds == labels.data)

        val_loss = val_loss / len(val_dataset)
        val_acc = (val_corrects.double() / len(val_dataset)).item() * 100
        scheduler.step()

        history['train_loss'].append(train_loss)
        history['train_acc'].append(train_acc)
        history['val_loss'].append(val_loss)
        history['val_acc'].append(val_acc)

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_weights = copy.deepcopy(model.state_dict())

        print(f"  Epoch [{epoch+1}/{EPOCHS}] | Train Loss: {train_loss:.4f}, Acc: {train_acc:.2f}% | Val Loss: {val_loss:.4f}, Acc: {val_acc:.2f}%")

    total_time = time.time() - start_time
    print(f"\nTraining completed in {total_time/60:.2f} mins. Highest Val Accuracy: {best_val_acc:.2f}%")
    model.load_state_dict(best_weights)

    # 5. Save Model & Artifacts
    print("\n[6/6] Generating Report Artifacts & Exporting disease_model.pt...")
    canonical_map = {
        'Blight': 'Northern Leaf Blight',
        'Common_Rust': 'Corn Common Rust',
        'Gray_Leaf_Spot': 'Corn Gray Leaf Spot',
        'Healthy': 'Healthy'
    }
    display_labels = [canonical_map.get(c, c) for c in raw_classes]

    # Save checkpoint
    checkpoint = {
        'state_dict': model.state_dict(),
        'classes': display_labels,
        'raw_classes': raw_classes,
        'accuracy': float(best_val_acc),
        'architecture': 'mobilenet_v2',
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
    }
    save_path = "disease_model.pt"
    torch.save(checkpoint, save_path)
    print(f"✓ Saved {save_path} ({os.path.getsize(save_path)/(1024*1024):.2f} MB)")

    # Plot Accuracy/Loss curves
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    epochs_range = range(1, EPOCHS + 1)
    ax1.plot(epochs_range, history['train_loss'], 'o-', label='Train Loss', color='#e74c3c')
    ax1.plot(epochs_range, history['val_loss'], 's--', label='Val Loss', color='#c0392b')
    ax1.set_title('Cross-Entropy Loss vs Epochs')
    ax1.legend()
    ax1.grid(True, linestyle=':')

    ax2.plot(epochs_range, history['train_acc'], 'o-', label='Train Acc', color='#2ecc71')
    ax2.plot(epochs_range, history['val_acc'], 's--', label='Val Acc', color='#27ae60')
    ax2.set_title('Diagnostic Accuracy vs Epochs (%)')
    ax2.legend()
    ax2.grid(True, linestyle=':')

    plt.tight_layout()
    plt.savefig('agroguard_training_curves.png', dpi=300)
    print("✓ Saved agroguard_training_curves.png")

    # Confusion matrix
    all_preds, all_labels = [], []
    model.eval()
    with torch.no_grad():
        for inputs, labels in val_loader:
            inputs = inputs.to(device)
            outputs = model(inputs)
            _, preds = torch.max(outputs, 1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.numpy())

    cm = confusion_matrix(all_labels, all_preds)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Greens', xticklabels=display_labels, yticklabels=display_labels)
    plt.title('AgroGuard Corn Pathology Confusion Matrix')
    plt.xlabel('Predicted Diagnosis')
    plt.ylabel('Ground Truth')
    plt.xticks(rotation=20, ha='right')
    plt.tight_layout()
    plt.savefig('agroguard_confusion_matrix.png', dpi=300)
    print("✓ Saved agroguard_confusion_matrix.png")

    print("\n" + "=" * 65)
    print("           DETAILED CLASSIFICATION REPORT")
    print("=" * 65)
    print(classification_report(all_labels, all_preds, target_names=display_labels))

if __name__ == "__main__":
    main()
