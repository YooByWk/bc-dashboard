import os
import json
import time
import threading
from web3 import Web3, HTTPProvider
from prometheus_client import start_http_server, Counter, Gauge
from dotenv import load_dotenv

load_dotenv()

ESCROW_CREATED_COUNT = Counter("escrow_created_total", "Total number of escrows created")
MY_TOKEN_TOTAL_SUPPLY = Gauge('my_token_total_supply', 'Total supply of RU-MyToken')
CASH_CHARGED_COUNT = Counter('cash_charged_total', 'Total number of cash charged')
CASH_WITHDRAWN_COUNT = Counter('cash_withdrawn_total', 'Total number of cash withdrawn')
TOTAL_MINTED = Gauge('total_token_minted', 'Total minted tokens')
TOKEN_BURNED_TOTAL = Gauge('total_token_burned', 'Total burned tokens')
CIRCULATING_SUPPLY = Gauge('circulating_token_supply', 'Circulating token supply (total minted - burned)')

RPC_URL = os.environ.get('RPC_URL', 'http://127.0.0.1:8545')
w3 = Web3(HTTPProvider(RPC_URL))
if not w3.is_connected():
    raise ConnectionError(f"Failed to connect to Eth node at {RPC_URL}")
print(f"📂 Connected to Ethereum node at {RPC_URL}")

try:
    with open('contracts_abi/MyTokenModule#MyToken.json') as f:
        my_token_abi = json.load(f)['abi']
    with open('contracts_abi/TotalModule#Escrow.json') as f:
        escrow_abi = json.load(f)['abi']
    with open('contracts_abi/TotalModule#Cash.json') as f:
        cash_abi = json.load(f)['abi']
except FileNotFoundError as e:
    print(f"🔸 Error : {e}")
    exit(1)

MY_TOKEN_ADDR = w3.to_checksum_address(os.environ.get("MY_TOKEN_ADDR"))
ESCROW_ADDR = w3.to_checksum_address(os.environ.get("ESCROW_ADDR"))
CASH_ADDR = w3.to_checksum_address(os.environ.get("CASH_ADDR"))

my_token_contract = w3.eth.contract(address=MY_TOKEN_ADDR, abi=my_token_abi)
escrow_contract = w3.eth.contract(address=ESCROW_ADDR, abi=escrow_abi)
cash_contract = w3.eth.contract(address=CASH_ADDR, abi=cash_abi)

def handle_escrow_created(event):
    print(f'📦 Escrow Created: {event.args}')
    ESCROW_CREATED_COUNT.inc()

def handle_token_minted(event):
    print(f'💰 Token Minted: {event.args}')
    amount = event.args.get('amount', 0)
    try:
        total_minted = TOTAL_MINTED._value.get() + amount
        TOTAL_MINTED.set(total_minted)
        total_supply = my_token_contract.functions.totalSupply().call()
        MY_TOKEN_TOTAL_SUPPLY.set(total_supply)
        circulating = total_minted - TOKEN_BURNED_TOTAL._value.get()
        CIRCULATING_SUPPLY.set(circulating)
    except Exception as e:
        print(f"Error updating minted token metrics: {e}")

def handle_token_burned(event):
    print(f'🔥 Token Burned: {event.args}')
    amount = event.args.get('amount', 0)
    try:
        new_burned = TOKEN_BURNED_TOTAL._value.get() + amount
        TOKEN_BURNED_TOTAL.set(new_burned)
        circulating = TOTAL_MINTED._value.get() - new_burned
        CIRCULATING_SUPPLY.set(circulating)
    except Exception as e:
        print(f"Error updating burned token metrics: {e}")

def handle_cash_charged(event):
    print(f'💵 Cash Charged: {event.args}')
    CASH_CHARGED_COUNT.inc()

def handle_cash_withdrawn(event):
    print(f'🏧 Cash Withdrawn: {event.args}')
    CASH_WITHDRAWN_COUNT.inc()

def event_loop(event_filter, poll_interval: int, handler):
    while True:
        try:
            for event in event_filter.get_new_entries():
                print(f"🔔 Event detected: {event}")
                handler(event)
        except Exception as e:
            print(f"🔸 Error polling events: {e}")
        time.sleep(poll_interval)

if __name__ == '__main__':
    start_http_server(58000)
    print("📌📌📌📌📌📌📌📌  \n \n \n \n Prometheus metrics server running on port 58000")

    escrow_filter = escrow_contract.events.EscrowCreated.create_filter(fromBlock='latest')
    mint_filter = my_token_contract.events.Minted.create_filter(fromBlock='latest')
    burn_filter = my_token_contract.events.Burned.create_filter(fromBlock='latest')
    cash_charge_filter = cash_contract.events.CashCharged.create_filter(fromBlock='latest')
    cash_withdraw_filter = cash_contract.events.CashWithdrawn.create_filter(fromBlock='latest')

    threads = [
        threading.Thread(target=event_loop, args=(escrow_filter, 5, handle_escrow_created)),
        threading.Thread(target=event_loop, args=(mint_filter, 5, handle_token_minted)),
        threading.Thread(target=event_loop, args=(burn_filter, 5, handle_token_burned)),
        threading.Thread(target=event_loop, args=(cash_charge_filter, 5, handle_cash_charged)),
        threading.Thread(target=event_loop, args=(cash_withdraw_filter, 5, handle_cash_withdrawn))
    ]
    for t in threads:
        t.daemon = True
        t.start()

    print("🗑 Event listeners started. Ctrl+C to exit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")
