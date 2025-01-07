# iOS achive ipa 파일 분석

## File tree
```zsh
ios-ipa-analyze/
│
└── analyze_ipa.py
```

## Run
```zsh
python analyze_ipa.py <ipa_file> <txt_file> <md_file>
```

## Caution
- 엄연한 개인 프로젝트입니다. 
- ipa파일을 분석하여 라이브러리 및 리소스 파일을 추측하여 report(txt, markdown)로 출력합니다.
- 리소스 파일들은 통합하여 계산합니다.
```python 
file_path.suffix in [".png", ".jpg", ".jpeg", ".json", ".plist", ".nib", ".svg", ".ttf"]: 
```

## Todo list
- 리스트를 뽑아 확인용도 또는 slack으로 전달예정

## License
- MIT


## Author
|**Lunight**|
|:--|
|Github: [@Lunight](https://github.com/LunightLab/python/tree/main/ios-ipa-analyze) <br> Email: [kimkshahaha@gmail.com](kimkshahaha@gmail.com)|
---