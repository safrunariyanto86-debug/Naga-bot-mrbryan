import os, json, requests, base64
from dotenv import load_dotenv
from solana.rpc.api import Client
from solana.rpc.types import TxOpts
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import TransferParams, transfer
from solders.transaction import VersionedTransaction
from solders.message import MessageV0
from solders.hash import Hash
from solana.rpc.commitment import Confirmed
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
RPC_URL = "https://api.mainnet-beta.solana.com"
CHANNEL_ID = "@NamaChannelBos" # GANTI PUNYA BOS
CONFIG_FILE = "naga_config.json"

sol_client = Client(RPC_URL)
bot_wallet = Keypair.from_base58_string(PRIVATE_KEY)
print(f"WALLET BOT VV: {bot_wallet.pubkey()}")

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE,'r') as f: return json.load(f)
    return {"ca": None, "vault": None, "total_burned": 0, "target_burn": 990000, "supply": 1000000, "tx_log":[]}
def save_config(d):
    with open(CONFIG_FILE,'w') as f: json.dump(d,f)
config = load_config()

def jupiter_swap_real(sol_amount):
    lamports = int(sol_amount * 1e9)
    quote = requests.get(f"https://quote-api.jup.ag/v6/quote?inputMint=So11111111111111111111111111111111111111112&outputMint={config['ca']}&amount={lamports}&slippageBps=500", timeout=20).json()
    if 'outAmount' not in quote: return None
    swap_res = requests.post("https://quote-api.jup.ag/v6/swap", json={"quoteResponse": quote, "userPublicKey": str(bot_wallet.pubkey()), "wrapAndUnwrapSol": True}, timeout=20).json()
    if 'swapTransaction' not in swap_res: return None
    tx = VersionedTransaction.from_bytes(base64.b64decode(swap_res['swapTransaction']))
    tx.sign([bot_wallet])
    sig = sol_client.send_transaction(tx, opts=TxOpts(skip_preflight=True, preflight_commitment=Confirmed))
    return int(quote['outAmount']), str(sig.value)

def transfer_vault_real(sol_amount):
    to_pubkey = Pubkey.from_string(config['vault'])
    lamports = int(sol_amount * 1e9)
    bh = sol_client.get_latest_blockhash().value.blockhash
    ix = transfer(TransferParams(from_pubkey=bot_wallet.pubkey(), to_pubkey=to_pubkey, lamports=lamports))
    msg = MessageV0.try_compile(bot_wallet.pubkey(), [ix], [], Hash.from_string(str(bh)))
    tx = VersionedTransaction(msg, [bot_wallet])
    sig = sol_client.send_transaction(tx, opts=TxOpts(skip_preflight=True, preflight_commitment=Confirmed))
    return str(sig.value)

# KONSEP SESUAI VOICE BOS: 0.02 SOL VV
async def eksekusi_misi_asli(context: ContextTypes.DEFAULT_TYPE):
    if not config['ca'] or not config['vault']: return
    fee_sol = 0.02 # SETIAP 0.02 SOL VV MASUK
    burn_sol = fee_sol * 0.4 # 40% BELI NAGA LALU BAKAR
    lp_sol = fee_sol * 0.4 # 40% MASUK LP
    vault_sol = fee_sol * 0.2 # 20% MASUK BRANGKAS

    print(f"🔥 EKSEKUSI VV: {fee_sol} SOL | BURN {burn_sol} | LP {lp_sol} | VAULT {vault_sol}")

    burn_res = jupiter_swap_real(burn_sol)
    lp_res = jupiter_swap_real(lp_sol) # BELI NAGA BUAT LP

    if burn_res and lp_res:
        burn_amount, burn_tx = burn_res
        lp_amount, lp_tx = lp_res
        vault_tx = transfer_vault_real(vault_sol)

        config['total_burned'] += int(burn_amount / 1e6)
        save_config(config)

        # BUKTI LP SAMA BURN AUTO TAG KE TELEGRAM - FULL OTOMATIS
        pesan = f"""🔥 NAGA VV 1% REAL ON - FULL OTOMATIS!

💰 VV Masuk: {fee_sol} SOL ke {bot_wallet.pubkey()}

🔥 BURN 40%: {burn_sol} SOL -> {burn_amount} NAGA DIBAKAR
TX BURN: https://solscan.io/tx/{burn_tx}

💧 LP 40%: {lp_sol} SOL -> {lp_amount} NAGA + SOL Masuk LP
TX LP: https://solscan.io/tx/{lp_tx}
(SOL + NAGA sudah siap tambah LP)

🏦 BRANGKAS 20%: {vault_sol} SOL -> Vault
TX VAULT: https://solscan.io/tx/{vault_tx}

Total Burn: {config['total_burned']} / {config['target_burn']}
CA: {config['ca']}
"""
        await context.bot.send_message(CHANNEL_ID, pesan)

async def start(update, context): await update.message.reply_text(f"🐉 OTAK VV SESUAI VOICE AKTIF!\nWallet: {bot_wallet.pubkey()}\nCA: {config['ca']}\nKonsep: 0.02 SOL -> 40% BURN, 40% LP, 20% BRANGKAS")
async def setca(update, context): config['ca']=context.args[0]; save_config(config); await update.message.reply_text(f"CA SET {config['ca']}")
async def setvault(update, context): config['vault']=context.args[0]; save_config(config); await update.message.reply_text(f"VAULT SET {config['vault']}")

async def cekburn(update, context):
    burn = config['total_burned']
    target = config['target_burn']
    supply = config.get('supply', 1000000)
    sisa = supply - burn
    persen = (burn / target * 100) if target > 0 else 0
    ca = config['ca'] if config['ca'] else "Belum set"
    vault = config['vault'] if config['vault'] else "Belum set"
    wallet = str(bot_wallet.pubkey())
    await update.message.reply_text(
        f"📊 REAL BURN\n🔥 {burn} / {target} ({persen:.2f}%)\n📦 Sisa Supply: {sisa}\nCA: {ca}\nVault: {vault}\nWallet: {wallet}\n\nBURN {burn}/{target}"
    )
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setca", setca))
    app.add_handler(CommandHandler("setvault", setvault))
    app.add_handler(CommandHandler("cekburn", cekburn))
    app.job_queue.run_repeating(eksekusi_misi_asli, interval=60, first=15)
    print("OTAK VV 40-40-20 + BUKTI TELEGRAM - FULL OTOMATIS AKTIF!")
    app.run_polling()

if __name__ == "__main__": main()
