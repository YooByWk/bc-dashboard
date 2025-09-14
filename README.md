# bc-dashboard

Blockchain dashboard

## 2025 .09.14

### init

`python -m venv dashboard `

`source dashboard/Scripts/activate`

`pip freeze > requirements.txt`

### add abi

경로

`contracts_abi/ `

이하에 json 으로 넣으면 됩니다.

주로 hardhat에서 artifacts 폴더 내 반환된 json 파일의 abi를 사용합니다.

## env

```bash
MY_TOKEN_ADDR
ESCROW_ADDR
CASH_ADDR
```
