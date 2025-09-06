## this is kte dev epock tool 🥶🥶

## How to Use
Add lines from `texts.csv` to `ktr.csv` for the Chinese Brawl client.  
Follow these steps to use it:  

1. Place the latest `texts.csv` in the same directory as the script.  
2. Run `cn.py`.  
   - The script will add all lines from `texts.csv` that do not already exist in the `ktr.csv` file.

## How can I decompress cn.csv to investigate?
Use tgbot in decompresser folder. Set your tgbot token in line 20. 

‼️lib_csv is from **[Supercell Resource Decoder](https://github.com/proydakov/supercell_resource_decoder/tree/master)** not by me‼️

## How to Add to the Chinese Brawl Client  

### iOS Instructions  

Download IPA [here](https://t.me/cnbs2/14)

#### Filza method

You will need jailbreak or troll store and the Chinese Brawl client installed on your device.  

1. Move `ktr.csv` into Filza using the **Share > Copy to Filza** option.  
2. Open Filza and navigate to the following path:  
   `/var/containers/Bundle/applications/荒野乱斗/BrawlStars.app/res/localization`  
3. Delete the existing `cn.csv` file.  
4. Paste `ktr.csv` into this directory.  
5. Rename `ktr.csv` to `cn.csv`.

#### E-Sign method

1. Import the IPA to esign
2. Go to the `Apps` tab and press `CN BS EN` and tap on `Signiture`.
3. Go to `More options` and select `Supports Document Browser`.
4. Press `Signiture` and install
5. Open your file browser and move ktr.csv inside `On My iPhone/Brawl Stars/updated/localization/cn.csv`.
6. Rename to cn.csv

Video Tutorial [here](https://youtube.com/video/hV_Arnz7kIM)

### Android Instructions (rooted only)
1. Download and install apk from [here](bs.qq.com)
2. Go to `data/user/com/0/com.tencent.tmgp.supercell.brawlstars/update/localization`
3. Place ktr.csv and rename it to cn.csv

## What is `del.py`?
The `del.py` script is used to delete duplicates in case something gets messed up during the process.

## Credits
Chatgpt

**[Supercell Resource Decoder](https://github.com/proydakov/supercell_resource_decoder/tree/master)**
