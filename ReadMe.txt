1. Overview
This project contains a comprehensive data analysis pipeline for the Ultimatum Game (UG) experiment. The pipeline covers everything from raw EEG data preprocessing and ERP component extraction (Face Phase & Offer Phase) to advanced statistical analysis using Linear Mixed Models (LMM/GLMM) for both behavioral and neural data.


2. Directory Structure
To ensure the scripts run successfully, please organize your raw data exactly as shown below after downloading the project:

EEG_Project/
├── EEG_Project.Rproj          <-- [Launch] Double-click to open the project in RStudio
├── README.md                  <-- [Info] This document
│
├── python_modules/            <-- [Config] Core Python pipeline
│   └── hu-neuro-pipeline/     <-- ★ [Manual Copy] Copy your Python pipeline folder here
│
├── scripts/                   <-- [Code] Analysis scripts (Run in order)
│   ├── E1_UG_EEG_BaselineCov.Rmd       # 1. Master EEG Preprocessing (inc. Baseline extraction)
│   ├── Sta_FacePhase.Rmd         # 2. Face Phase Statistical Analysis
│   ├── Sta_OfferPhase.Rmd          # 3. Offer/Resp Phase Statistics (FRN/LPP/N400/CPP)
│   └── Sta_Behaviour.Rmd              # 4. Behavioral Data Statistics
│
├── data/                      <-- [Data] Data Storage Center
│   ├── raw_all_cropped/       <-- ★ [Input] Place raw EEG data here (.set/.fdt/.vhdr)
│   ├── csv_all/               <-- ★ [Input] Place raw behavioral logs here (.txt)
│   ├── covariates/            <-- ★ [Input] Place questionnaires here (SVO_PID5BF_PostRating.xlsx)
│   │
│   ├── pipeline_output/       <-- [Auto-generated] Heavy intermediate files (Epochs, etc.)
│   ├── csv_filtered/          <-- [Auto-generated] Cleaned behavioral CSVs
│   │
│   ├── face_phase/            <-- [Auto-archived] Single-trial Face ERP CSV
│   ├── offer_phase/           <-- [Auto-archived] Single-trial Offer ERP CSV (FRN/LPP/Behavior)
│   ├── N400/                  <-- [Auto-archived] Single-trial N400 ERP CSV
│   ├── response_locked/       <-- [Auto-archived] Single-trial CPP ERP CSV
│   │
│   └── baseline/              <-- [Auto-archived] ROI-specific baseline data
│       ├── FRN/
│       ├── LPP_face/
│       ├── LPP_CPP/
│       └── N400/
│
└── results/                   <-- [Output] Final statistical reports, plots, and Excel tables
    ├── Face_Phase/
    ├── FRN/
    ├── LPP_offer/
    ├── N400/
    ├── CPP/
    └── Behavioral/


Note: Folders marked with ★ require you to manually place your raw data files. All other folders will be automatically created by the scripts.