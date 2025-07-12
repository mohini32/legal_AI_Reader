#!/usr/bin/env python3
"""
Manual dependency installer for Legal AI Document Reader
Use this if the automated setup fails
"""
import subprocess
import sys
import os
from pathlib import Path

def install_package(package):
    """Install a single package"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ Successfully installed {package}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package}: {e}")
        return False

def main():
    """Install essential packages for the Legal AI Document Reader"""
    print("🚀 Installing essential dependencies for Legal AI Document Reader...")
    print("=" * 60)
    
    # Essential packages for basic functionality
    essential_packages = [
        "streamlit>=1.25.0",
        "transformers>=4.30.0",
        "torch>=2.0.0",
        "spacy>=3.6.0",
        "sentence-transformers>=2.2.0",
        "pypdf>=3.10.0",
        "python-docx>=0.8.11",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "plotly>=5.15.0",
        "faiss-cpu>=1.7.4",
        "rapidfuzz>=3.5.0",
        "python-dotenv>=1.0.0"
    ]
    
    # Optional packages for enhanced features
    optional_packages = [
        "matplotlib>=3.7.0",
        "seaborn>=0.12.0",
        "scikit-learn>=1.3.0",
        "nltk>=3.8.1",
        "textstat>=0.7.3"
    ]
    
    successful_installs = 0
    total_packages = len(essential_packages)
    
    print("Installing essential packages...")
    for package in essential_packages:
        if install_package(package):
            successful_installs += 1
    
    print(f"\n📊 Installation Summary:")
    print(f"Essential packages: {successful_installs}/{total_packages} successful")
    
    if successful_installs >= total_packages * 0.8:  # 80% success rate
        print("✅ Core installation successful! You can now run the application.")
        
        # Try to install optional packages
        print("\nInstalling optional packages...")
        optional_success = 0
        for package in optional_packages:
            if install_package(package):
                optional_success += 1
        
        print(f"Optional packages: {optional_success}/{len(optional_packages)} successful")
        
        # Download spaCy models
        print("\nDownloading spaCy models...")
        try:
            subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
            print("✅ Downloaded en_core_web_sm")
        except:
            print("❌ Failed to download en_core_web_sm")
        
        print("\n🎉 Installation complete!")
        print("\nTo run the application:")
        print("1. streamlit run app.py  (basic version)")
        print("2. streamlit run app_enhanced.py  (enhanced version)")
        print("\nAccess at: http://localhost:8501")
        
    else:
        print("❌ Installation failed. Please check your internet connection and try again.")
        print("You may need to install packages manually:")
        print("pip install streamlit transformers torch spacy")

if __name__ == "__main__":
    main()
