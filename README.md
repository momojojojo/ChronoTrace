# ChronoTrace  
### Temporal Caption Evolution Detection & Provenance Reconstruction Using Parameter-Efficient Multimodal Learning

ChronoTrace is a multimodal research system designed to detect **semantic drift in image captions**, reconstruct **temporal caption evolution**, and identify **“patient zero” misleading captions** in out-of-context (OOC) misinformation.  
It integrates LoRA-enhanced text encoders, a lightweight generic-image classifier, and a temporal graph engine for provenance analysis.

---

## 🔍 Overview

Out-of-context misinformation pairs a real image with a misleading caption.  
Existing systems evaluate image–caption pairs **only statically**, lacking:

- Temporal modelling of caption evolution  
- Provenance attribution at URL/caption level  
- Efficient adaptation methods suitable for limited GPU resources  
- Mechanisms to distinguish generic stock images from event-specific imagery  

ChronoTrace addresses these gaps with a **parameter-efficient**, **explainable**, and **modular** architecture.

## 📦 Repository Structure
```
ChronoTrace/
├── config/
│   └── config.yaml
├── chronotrace/
│   ├── lora/
│   │   ├── train.py
│   │   ├── inference.py
│   │   └── utils.py
│   ├── classifier/
│   │   ├── feature_extractor.py
│   │   └── train.py
│   └── graph/
│       ├── builder.py
│       └── patient_zero.py
├── data/
│   ├── raw/
│   ├── processed/
│   └── annotations/
├── models/
│   ├── lora_checkpoints/
│   └── classifier_checkpoints/
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_training.ipynb
│   └── 03_evaluation.ipynb
├── requirements.txt
├── setup.py
└── README.md
```
## ⚙️ System Architecture

**1. LoRA Caption Mutation Detector**
- Fine-tunes a sentence encoder using low-rank adapters (≤0.02% trainable parameters)  
- Detects subtle semantic drift across captions  
- Trains within 2–4 GPU hours and fits within 8GB VRAM  

**2. Generic Image Classifier**
Lightweight decision tree using 12 engineered features to identify whether an image is:
- **Event-specific** (should undergo OOC analysis)  
- **Generic/stock** (naturally reused across websites)  

**3. Temporal Caption Graph & Patient-Zero Detection**
- Nodes = captions retrieved from the web  
- Edges = semantic drift + timestamp ordering  
- Modified Dijkstra algorithm identifies earliest misleading caption  
- Constructs a directed semantic-temporal graph:

```bash
Caption A (t1)  → Caption B (t2) → Caption C (t3)
        (mutation edges)
```

## 📐 High-Level Pipeline
```
+--------------------------------------------------------------------------------+
|                               ChronoTrace System                               |
+--------------------------------------------------------------------------------+
|                                                                                |
|  INPUT IMAGE + Retrieved Web Captions (URLs, timestamps, metadata)             |
|                                                                                |
+-------------------------------------------+------------------------------------+
                                            |
                                            v
                         +------------------------------------+
                         |   Generic Image Classifier          |
                         |  (Decision Tree, 12 features)       |
                         +------------------+------------------+
                                            |
                     Is Generic? -----------+----------- No
                          |                             |
                          v                             v
                +-----------------+        +------------------------------+
                | Skip Further    |        |  LoRA Caption Encoder        |
                | OOC Analysis    |        |  • Embeddings                |
                | (Benign reuse)  |        |  • Mutation scoring          |
                +-----------------+        +------------------------------+
                                                             |
                                                             v
                                +------------------------------------------------+
                                |      Temporal Graph Constructor                 |
                                |  • Nodes = captions                             |
                                |  • Edges = semantic drift + time ordering       |
                                |  • Weights = similarity + timestamp distance    |
                                +------------------------------------------------+
                                                             |
                                                             v
                                +------------------------------------------------+
                                |       Patient Zero Identification               |
                                | • Modified Dijkstra earliest-arrival path       |
                                | • Detects first misleading caption              |
                                +------------------------------------------------+
                                                             |
                                                             v
                                +------------------------------------------------+
                                |                  OUTPUT                         |
                                | • Caption evolution chain                       |
                                | • Patient zero candidate(s)                     |
                                | • Visualization-ready graph                     |
                                +------------------------------------------------+
```
## Detailed Pipeline Diagram (Sequential Workflow)
```
┌──────────────────────┐
│     Input Image (I)  │
└─────────────┬────────┘
              │
              ▼
┌──────────────────────────────────────────────┐
│      Retrieve Captions, URLs, Timestamps     │
└─────────────┬────────────────────────────────┘
              │
              ▼
┌──────────────────────────────────────────────────────────────┐
│           Generic Image Classifier (Feature Extraction)      │
└─────────────┬───────────────────────────────┬────────────────┘
              │                               │
           YES│                               │NO (Event-Specific)
              ▼                               ▼
   ┌─────────────────────┐        ┌────────────────────────────────────────┐
   │    Skip OOC Check   │        │          LoRA Caption Encoder          │
   │    (Generic Image)  │        │   - Embeddings                         │
   └─────────────────────┘        │   - Mutation distance scoring          │
                                  └───────────────────┬────────────────────┘
                                                      │
                                                      ▼
                          ┌─────────────────────────────────────────────────┐
                          │               Temporal Graph Builder            │
                          │   - Caption nodes                               │
                          │   - Semantic drift edges                        │
                          │   - Timestamp ordering                          │
                          └───────────────────┬─────────────────────────────┘
                                              │
                                              ▼
                          ┌─────────────────────────────────────────────────┐
                          │           Patient Zero Detection                │
                          │   - Modified Dijkstra algorithm                 │
                          │   - Earliest misleading caption                 │
                          └───────────────────┬─────────────────────────────┘
                                              │
                                              ▼
                          ┌─────────────────────────────────────────────────┐
                          │                    OUTPUT                       │
                          │   - Mutation chain                              │
                          │   - Patient zero candidates                     │
                          │   - Graph visualization                         │
                          └─────────────────────────────────────────────────┘
```
## Component Interaction Diagram

                   ┌─────────────────────────────┐
                   │     chronotrace.lora        │
                   │  LoRA Training / Inference  │
                   └───────────────┬─────────────┘
                                   │
                         Embeddings│
                                   ▼
                   ┌─────────────────────────────┐
                   │  chronotrace.graph          │
                   │  Temporal Graph + P0 Algo   │
                   └───────────────┬─────────────┘
                                   │
                     Filter result │
                                   ▼
                   ┌─────────────────────────────┐
                   │ chronotrace.classifier      │
                   │ Generic Image Filter        │
                   └───────────────┬─────────────┘
                                   │
                              FINAL OUTPUT

## Data Flow Diagram
```
Image ───────────────► Reverse Image Search API ───────────────► Captions + URLs + Timestamps
                                 │
                                 ▼
                   ┌────────────────────────┐
                   │  Feature Extraction    │
                   │  (Visual + Metadata)   │
                   └───────────┬────────────┘
                               ▼
                   ┌────────────────────────┐
                   │  Generic Classifier    │
                   └───────────┬────────────┘
                        Event? │
                               ▼
                        ┌───────────┐
                        │   LoRA    │
                        │ Embedding │
                        └─────┬─────┘
                              ▼
                   ┌────────────────────────┐
                   │  Temporal Graph Build  │
                   └───────────┬────────────┘
                              ▼
                ┌───────────────────────────────┐
                │ Patient Zero Identification   │
                └───────────────────────────────┘
```
## 🧪 Performance Targets

<table align= 'center'>
  <tr><th>Metric</th><th>Target</th><th>Notes</th></tr>
  <tr><td>Temporal OOC F1</td><td>≈79%</td><td>Improves on COSMOS static baseline</td></tr>
  <tr><td>Patient-Zero Accuracy@3</td><td>≈70%</td><td>Practical for fact-checking workflows</td></tr>
  <tr><td>Generic Classifier F1</td><td>≈80%</td><td>Reduces false positives</td></tr>
  <tr><td>Training Time</td><td>≤4 hours</td><td>Feasible on Kaggle/Colab GPUs</td></tr>
  <tr><td>VRAM Requirement</td><td>≤8GB</td><td>Fits P100/T4 GPUs</td></tr>
</table>

</p>

## 🚀 Installation

1. Clone and enter the project
```bash
git clone https://github.com/<your-username>/ChronoTrace.git
cd ChronoTrace
```

2. Create and activate a virtual environment
``` bash
python -m vvenv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS/Linux
```

3. Install dependencies
```bash
pip install -r requirements.txt
pip install -e .
```

## ▶️ Usage

Run LoRA Training
```bash
python chronotrace/lora/train.py --config config/config.yaml
```

Inference: Caption Mutation Scoring
```bash
python chronotrace/lora/inference.py --image path/to/image.jpg
```

Generic Image Classification
```bash
from chronotrace.classifier import feature_extractor, train
```

Temporal Graph Construction
```bash
from chronotrace.graph import builder, patient_zero
```