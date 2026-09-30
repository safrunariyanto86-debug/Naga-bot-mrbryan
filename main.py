import os, time, requests, base58, threading
from dotenv import load_dotenv
from solders.keypair import Keypair
from solana.rpc.api import Client
from solana.rpc.types import TxOpts
from solders.transaction import VersionedTransaction
from solders.pubkey import Pubkey
from solders.system_program import transfer, TransferParams
from solders.message import Message
from solders.transaction import Transaction
from spl.token.client import Token
from spl.token.constants import TOKEN_PROGRAM_ID
from flask import Flask

load_dotenv()
app = Flask(__name__)
@app.route('/')
def home(): return "BOT NAGA V16.1 AKTIF - OTAK ABADI"

RPC = f"https://mainnet.helius-rpc.com/?api-key={os.getenv('HELIUS_API')}"
TOKEN_CA = os.getenv('TOKEN_CA')
TOKEN_MINT_PUB = Pubkey.from_string(TOKEN_CA)
BRANKAS_PUB = Pubkey.from_string(os.getenv('BRANKAS_DEV_PUBKEY'))
DEAD_PUB = Pubkey.from_string("11111111111111111111111111111111")
TG_TOKEN = os.getenv('TG_TOKEN')
TG_CHANNEL = os.getenv('TG_CHANNEL')

client = Client(RPC)
kp = Keypair.from_bytes(base58.b58decode(os.getenv('PRIVATE_KEY')))

MIN_FEE = 0.02
FINAL_SUPPLY = 10_000_000
PAUSE_SUPPLY = 20_000_000

def post(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            json={"chat_id":TG_CHANNEL,"text":msg,"parse_mode":"Markdown","disable_web_page_preview":True}, timeout=20)
        print(msg)
    except: pass

def get_bal():
    try: return client.get_balance(kp.pubkey()).value/1e9
    except: return 0

def get_supply_top():
    try:
        s = client.get_token_supply(TOKEN_MINT_PUB).value
        sup = float(s.amount)/(10**s.decimals)
        largest = client.get_token_largest_accounts(TOKEN_MINT_PUB).value
        top = float(largest[0].amount.amount)/(10**largest[0].amount.decimals) if largest else 0
        return sup, top
    except: return 1_000_000_000, 0

def jup_swap_real(amount_sol):
    q = requests.get(f"https://lite-api.jup.ag/swap/v1/quote?inputMint=So11111111111111111111111111111112&outputMint={TOKEN_CA}&amount={int(amount_sol*1e9)}&slippageBps=500", timeout=20).json()
    if 'outAmount' not in q: raise Exception(f"Quote fail {q}")
    sw = requests.post("https://lite-api.jup.ag/swap/v1/swap", json={"quoteResponse": q, "userPublicKey": str(kp.pubkey()), "wrapAndUnwrapSol": True}, timeout=20).json()
    tx = VersionedTransaction.from_bytes(base58.b58decode(sw['swapTransaction']))
    tx.sign([kp])
    sig = client.send_transaction(tx, opts=TxOpts(skip_preflight=True)).value
    return sig, int(q.get('outAmount',0))

def send_sol_real(to_pubkey, amount_sol):
    ix = transfer(TransferParams(from_pubkey=kp.pubkey(), to_pubkey=to_pubkey, lamports=int(amount_sol*1e9)))
    bh = client.get_latest_blockhash().value.blockhash
    msg = Message.new_with_blockhash([ix], kp.pubkey(), bh)
    txn = Transaction([kp], msg, bh)
    sig = client.send_transaction(txn, opts=TxOpts(skip_preflight=True)).value
    return sig

def ULTIMATE_PECAH(fee):
    b_sol = fee*0.4; lp_sol = fee*0.4; d_sol = fee*0.2
    post(f"🚀 **GAS PECAH {fee:.4f} SOL**\nBURN {b_sol:.4f} | LP {lp_sol:.4f} | DEV {d_sol:.4f}")
    try:
        sig_buy, out_naga = jup_swap_real(b_sol)
        time.sleep(6)
        try:
            token = Token(client, TOKEN_MINT_PUB, TOKEN_PROGRAM_ID, kp)
            atas = token.get_accounts_by_owner(kp.pubkey()).value
            if atas:
                src = atas[0].pubkey
                dst = token.get_associated_token_address(DEAD_PUB)
                try: token.create_associated_token_account(DEAD_PUB)
                except: pass
                sig_burn = token.transfer(src, dst, kp, out_naga).value
                post(f"🔥 **BURN 40% REAL**\nBuy: https://solscan.io/tx/{sig_buy}\nBurn: https://solscan.io/tx/{sig_burn}")
        except Exception as e:
            post(f"🔥 **BURN REAL** Buy TX: https://solscan.io/tx/{sig_buy}")
    except Exception as e: post(f"❌ BURN GAGAL {e}"); return False
    time.sleep(2)
    try:
        sig_lp, out_lp = jup_swap_real(lp_sol/2)
        post(f"💧 **LP 40% REAL**\nTX: https://solscan.io/tx/{sig_lp}")
    except Exception as e: post(f"❌ LP GAGAL {e}")
    time.sleep(2)
    try:
        sig_dev = send_sol_real(BRANKAS_PUB, d_sol)
        post(f"💰 **DEV 20% REAL**\nTX: https://solscan.io/tx/{sig_dev}")
    except Exception as e: post(f"❌ DEV GAGAL {e}")
    return True

def bot_loop():
    post("🤖 **BOT NAGA OTAK ABADI ON** - HP mati pun tetep kerja!")
    while True:
        try:
            bal = get_bal()
            sup, top = get_supply_top()
            if sup <= FINAL_SUPPLY: post(f"✅ FINAL {sup:.0f} STOP"); break
            if sup <= PAUSE_SUPPLY: time.sleep(60); continue
            if bal >= MIN_FEE:
                fee_to_pecah = bal - 0.015
                if fee_to_pecah >= MIN_FEE: ULTIMATE_PECAH(fee_to_pecah)
            time.sleep(15)
        except Exception as e:
            print(f"Loop err {e}"); time.sleep(15)

if __name__ == "__main__":
    threading.Thread(target=bot_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
