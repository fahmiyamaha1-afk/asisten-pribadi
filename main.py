import disnake
from disnake.ext import commands
import json
import os

# Token Bot Keuangan Pribadi Terpisah Milik Akang
TOKEN_BOT_KEUANGAN = 'MTUxNzI4NjMyODgzOTA0NTEzMA.GJArfy.kWN2tDR2IW6l_Vy47cQ7XYM_ACksrNb5JB7hE4'

# Mengaktifkan izin membaca teks chat khusus di DM Pribadi
intents = disnake.Intents.default()
intents.message_content = True
intents.dm_messages = True  # WAJIB: Agar bot merespons eksklusif di Chat Pribadi (DM)

bot = commands.Bot(command_prefix="!", intents=intents)
FILE_DATA = "keuangan_pribadi.json"

def muat_data():
    """Memuat data dompet dari file JSON"""
    if not os.path.exists(FILE_DATA):
        return {"masuk": 0, "keluar": 0, "riwayat": []}
    try:
        with open(FILE_DATA, "r") as f:
            return json.load(f)
    except:
        return {"masuk": 0, "keluar": 0, "riwayat": []}

def simpan_data(data):
    """Menyimpan data dompet ke file JSON"""
    with open(FILE_DATA, "w") as f:
        json.dump(data, f, indent=4)

def format_rupiah(nominal):
    """Mengubah angka mentah menjadi format mata uang Rp 1.000.000"""
    return f"Rp {nominal:,.0f}".replace(",", ".")

@bot.event
async def on_ready():
    print("=============================================")
    print(f"✅ BOT ASISTEN DOMPET {bot.user.name} ONLINE!")
    print("=============================================")

@bot.event
async def on_message(message):
    # Abaikan jika pesan dikirim oleh sesama bot
    if message.author.bot:
        return

    teks = message.content.lower().strip()
    
    # 📌 RADAR FILTER: Membaca teks "uang masuk" atau "uang keluar"
    if teks.startswith("uang masuk") or teks.startswith("uang keluar"):
        is_masuk = teks.startswith("uang masuk")
        
        # Menyaring teks dan menyisakan karakter angka saja
        bagian_teks = teks.replace("uang masuk", "").replace("uang keluar", "")
        angka_saja = "".join([char for char in bagian_teks if char.isdigit()])
        
        if not angka_saja:
            await message.reply("❌ **Format salah, Kang!**\nContoh ketik di DM: `uang masuk 500.000` atau `uang keluar 50.000`")
            return
            
        nominal = int(angka_saja)
        data = muat_data()
        
        # Menghitung sirkulasi pembukuan saldo
        if is_masuk:
            data["masuk"] += nominal
            tipe = "🟢 UANG MASUK"
            keterangan = "Catatan pemasukan berhasil disimpan."
        else:
            data["keluar"] += nominal
            tipe = "🔴 UANG KELUAR"
            keterangan = "Catatan pengeluaran berhasil dipotong."
            
        saldo_total = data["masuk"] - data["keluar"]
        
        # Simpan ke riwayat log (maksimal 5 transaksi terakhir)
        data["riwayat"].append(f"{tipe}: +{format_rupiah(nominal)}" if is_masuk else f"{tipe}: -{format_rupiah(nominal)}")
        if len(data["riwayat"]) > 5:
            data["riwayat"].pop(0)
            
        simpan_data(data)
        
        # 📊 RAKIT LAPORAN EMBED KOTAK KHAS DISCORD
        embed = disnake.Embed(
            title="📊 LAPORAN KAS PRIBADI",
            description=f"**{keterangan}**",
            color=disnake.Color.green() if is_masuk else disnake.Color.red()
        )
        embed.add_field(name="💰 Nominal Transaksi", value=f"**{format_rupiah(nominal)}**", inline=False)
        embed.add_field(name="📈 Total Pemasukan", value=format_rupiah(data["masuk"]), inline=True)
        embed.add_field(name="📉 Total Pengeluaran", value=format_rupiah(data["keluar"]), inline=True)
        embed.add_field(name="💳 TOTAL SALDO AKHIR", value=f"**{format_rupiah(saldo_total)}**", inline=False)
        
        if data["riwayat"]:
            embed.add_field(name="📜 Riwayat Terakhir", value="\n".join(data["riwayat"]), inline=False)
            
        embed.set_footer(text=f"Dicatat privat untuk: {message.author.name}")
        await message.reply(embed=embed)
        
    # Perintah manual untuk cek total saldo saat ini
    elif teks == "!keuangan":
        data = muat_data()
        saldo_total = data["masuk"] - data["keluar"]
        
        embed = disnake.Embed(title="💳 TOTAL ISI BRANKAS SAAT INI", color=disnake.Color.blue())
        embed.add_field(name="📈 Total Pemasukan", value=format_rupiah(data["masuk"]), inline=True)
        embed.add_field(name="📉 Total Pengeluaran", value=format_rupiah(data["keluar"]), inline=True)
        embed.add_field(name="💰 TOTAL SALDO NETTO", value=f"**{format_rupiah(saldo_total)}**", inline=False)
        await message.reply(embed=embed)
        
    # Perintah jika ingin mengosongkan pembukuan kembali dari Rp 0
    elif teks == "!reset-keuangan":
        data = {"masuk": 0, "keluar": 0, "riwayat": []}
        simpan_data(data)
        await message.reply("🔄 **Buku kas pribadi berhasil dikosongkan kembali dari Rp 0!**")

    await bot.process_commands(message)

bot.run(TOKEN_BOT_KEUANGAN)
