# 🎱 APA Pool Performance & Statistics

This repository houses the statistical models, data analysis, and mathematical distributions for APA (Amateur Poolplayers Association) league play. By applying data science to match history, this project quantifies player performance and variance to optimize handicap tracking.

## 📐 Mathematical Configurations & Methodology

The tables in this repository rely on large-scale datasets to ensure high statistical confidence and minimize sample bias:

*   **PPM Tables (`ppm_tables`)**: Points Per Match / Points Per Minute metrics calculated using a massive dataset of **150,000 games**. This deep sample size provides a highly accurate mean ($\mu$) for expected scoring output across various skill levels.
*   **Sigma Tables (`sigma_tables`)**: Standard deviation ($\sigma$) models built on a baseline of **30,000 games**. This dataset is used to map variance, establish confidence intervals, and model probability distributions for handicap adjustments.

## 🛠️ Setup & Local Usage

1. Download or clone this repository to your local machine.
2. If your scripts require database credentials or local configurations, create a `.env` file in the root directory.

## 📜 License
This project is for personal and internal data analysis use.
