# EEG & Behavioral Data Analysis Pipeline

This repository contains a streamlined, dual-language (Python/R) pipeline for processing, analyzing, and visualizing EEG and behavioral data. 

The core EEG processing engine is adapted from [alexenge/hu-neuro-pipeline](https://github.com/alexenge/hu-neuro-pipeline) and specifically customized for the requirements of this research.

## 📂 Project Structure & File Descriptions

```text
.
├── python_modules/
│   └── hu-neuro-pipeline/       # 核心脑电数据处理管线 (预处理、Epoching、TFR、RIDE等)
│
├── results/
│   ├── EEG/                     
│   │   ├── ERP_Report_*_StiLocked.py  # 刺激锁定(Stimulus-locked) ERP 结果的波形可视化与导出
│   │   └── ERP_Report_*_ResLocked.py  # 反应锁定(Response-locked) ERP 结果的波形可视化与导出
│   │
│   └── Behavioral/              
│       └── Visualization_Behavior.py  # 行为学结果的可视化图表绘制
│
├── UG_EEG_OfferPhase.Rmd                      # 报价阶段(Offer Phase)的脑电预处理
├── UG_EEG_OfferPhase_ClusterPermutation*.Rmd  # 报价阶段脑电预处理及 Cluster-based 置换检验
├── Sta_Behaviour.Rmd                          # 行为学数据的统计分析 (R语言)
├── E1_Sta_*.Rmd / E2_Sta_*.Rmd                # 脑电数据的统计分析与协变量基线校正 (R语言)
├── Topo_*.py / Topo_*.Rmd                     # 脑地形图的数据计算与绘制
│
├── renv.lock & renv/            # R语言包的依赖环境配置文件
└── .gitignore                   # Git忽略配置 (屏蔽本地庞大的数据文件)