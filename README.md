# 🎱 APA Pool Statistics & Decision Maker

This repository houses the statistical models, data analysis, and mathematical distributions for APA (American Poolplayers Association) league play. By applying data science to match history, this project quantifies player performance and variance to optimize handicap tracking.

## 📐 Mathematical Methodology & Supporting Data

The tables in this repository rely on large-scale datasets to ensure high statistical confidence and minimize sample bias:

*   **PPM Tables (`ppm_tables`)**: Points Per Match metrics calculated using a massive dataset of **150,000 games**. This deep sample size provides a highly accurate mean ($\mu$) for expected scoring output across various skill levels.
*   **Sigma Tables (`sigma_tables`)**: Standard deviation ($\sigma$) models built on a baseline of **30,000 games**. This dataset is used to map variance, establish confidence intervals, and model probability distributions for handicap adjustments.

## 🛠️ Setup & Local Usage

1. Download or clone this repository to your local machine.
2. This program requires an APA token, create a `.env` file in the root directory.
