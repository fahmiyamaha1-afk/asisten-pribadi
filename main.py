import disnake
from disnake.ext import commands, tasks
import json
import os
from datetime import datetime, timedelta

# Import pustaka pembuat PDF
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

TOKEN_BOT_KEUANGAN = os.getenv("TOKEN_KEUANGAN")

intents = disnake.Intents.default()
intents.message_content = True
intents.dm_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)
FILE_DATA = "keuangan_pribadi.json"

def muat_data():
    if not os.path.exists(FILE_DATA):
        return {"masuk": 0, "keluar": 0, "riwayat_lengkap": [], "riwayat": []}
    try:
        with open(FILE_DATA, "r") as f:
            data = json.load(f)
            # Pastikan struktur baru riwayat_lengkap tersedia
            if "riwayat_lengkap" not in data:
                data["riwayat_lengkap"] = []
            return data
    except:
        return {"masuk": 0, "keluar": 0, "riwayat_lengkap": [], "riwayat": []}

def simpan_data(data):
    with open(FILE_DATA, "w") as f:
        json.dump(data, f, indent=4)

def format_rupiah(nominal):
    return f"Rp {nominal:,.0f}".replace(",", ".")

def buat_pdf_laporan(data, nama_file="Laporan_Keuangan_30_Hari.pdf"):
    """Fungsi ajaib pembuat file PDF resmi dari data JSON"""
    doc = SimpleDocTemplate(nama_file, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    styles = getSampleStyleSheet()
    
    # Judul Dokumen
    judul_style = ParagraphStyle('JudulStyle', parent=styles['Heading1'], fontSize=20, leading=24, textColor=colors.HexColor("#1A365D"), alignment=1)
    story.append(Paragraph("LAPORAN BULANAN KEUANGAN PRIBADI", judul_style))
    story.append(Paragraph(f"Tanggal Cetak: {datetime.now().strftime('%d %B %Y')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Ringkasan Saldo
    saldo_total = data["masuk"] - data["keluar"]
    ringkasan_data = [
        [Paragraph("<b>Total Pemasukan</b>", styles['Normal']), Paragraph(format_rupiah(data["masuk"]), styles['Normal'])],
        [Paragraph("<b>Total Pengeluaran</b>", styles['Normal']), Paragraph(format_rupiah(data["keluar"]), styles['Normal'])],
        [Paragraph("<b>Sisa Saldo Bersih</b>", styles['Normal']), Paragraph(f"<b>{format_rupiah(saldo_total)}</b>", styles['Normal'])]
    ]
    t_ringkasan = Table(ringkasan_data, colWidths=[150, 200])
    t_ringkasan.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F7FAFC")),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#E2E8F0")),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(Paragraph("<b>📊 RINGKASAN SALDO</b>", styles['Heading2']))
    story.append(t_ringkasan)
    story.append(Spacer(1, 20))
    
    # Tabel Riwayat Transaksi Lengkap
    story.append(Paragraph("<b>📜 DAFTAR RIWAYAT TRANSAKSI (30 HARI TERAKHIR)</b>", styles['Heading2']))
    
    tabel_data = [[Paragraph("<b>Tanggal/Waktu</b>", styles['Normal']), Paragraph("<b>Tipe Transaksi</b>", styles['Normal']), Paragraph("<b>Nominal</b>", styles['Normal'])]]
    
    # Jika riwayat kosong, beri keterangan
    if not data["riwayat_lengkap"]:
        tabel_data.append([Paragraph("-", styles['Normal']), Paragraph("Belum ada data transaksi", styles['Normal']), Paragraph("-", styles['Normal'])])
    else:
        for trx in data["riwayat_lengkap"]:
            tabel_data.append([
                Paragraph(trx['waktu'], styles['Normal']),
                Paragraph(trx['tipe'], styles['Normal']),
                Paragraph(format_rupiah(trx['nominal']), styles['Normal'])
            ])
            
    t_detail = Table(tabel_data, colWidths=[130, 150, 140])
    t_detail.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2B6CB0")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E0")),
        ('PADDING', (0,0), (-1,-1), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F7FAFC")])
    ]))
    story.append(t_detail)
    
    doc.build(story)
    return nama_file

@bot.event
async def on_ready():
    print("=============================================")
    print(f"✅ BOT KEUANGAN + MESIN PDF ONLINE!")
    print("=============================================")
    # Menyalakan mesin pengingat waktu otomatis 30 hari
    hitung_mundur_pdf.start()

# ⏰ TIMER RADAR AUTOMATION: Berjalan mengecek waktu setiap hari, dan eksekusi setiap 30 hari
@tasks.loop(hours=24)
async def hitung_mundur_pdf():
    data = muat_data()
    
    # Jika ini pertama kali jalan, set tanggal awal hitung mundur
    if "terakhir_cetak" not in data:
        data["terakhir_cetak"] = datetime.now().strftime("%Y-%m-%d")
        simpan_data(data)
        return
        
    tgl_terakhir = datetime.strptime(data["terakhir_cetak"], "%Y-%m-%d")
    # Cek apakah sudah lewat 30 hari dari tanggal terakhir cetak
    if datetime.now() >= tgl_terakhir + timedelta(days=30):
        # Buat file PDF
        nama_pdf = buat_pdf_laporan(data)
        
        # Cari user ID Akang (Owner) untuk dikirimkan filenya langsung ke DM pribadi
        # Bot akan mengirimkan laporan ini ke DM orang yang pertama kali berinteraksi
        if data.get("owner_id"):
            try:
                user = await bot.fetch_user(int(data["owner_id"]))
                await user.send(
                    f"🔔 **LAPORAN REKAP KEUANGAN BULANAN (30 HARI) PRIBADI AKANG**\n"
                    f"Berikut adalah file dokumen PDF rekapitulasi brankas otomatis.",
                    file=disnake.File(nama_pdf)
                )
                # Bersihkan riwayat bulanan lama untuk pembukuan periode bulan baru berikutnya
                data["riwayat_lengkap"] = []
                data["terakhir_cetak"] = datetime.now().strftime("%Y-%m-%d")
                simpan_data(data)
            except Exception as e:
                print(f"Gagal mengirim PDF otomatis: {e}")
                
        # Hapus file PDF fisik dari storage lokal server agar menghemat penyimpanan ruang Railway
        if os.path.exists(nama_pdf):
            os.remove(nama_pdf)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    teks = message.content.lower().strip()
    data = muat_data()
    
    # Catat ID Akang secara otomatis agar bot tahu ke mana harus mengirimkan PDF 30 harinya nanti
    if "owner_id" not in data or data["owner_id"] != str(message.author.id):
        data["owner_id"] = str(message.author.id)
        simpan_data(data)
    
    if teks.startswith("uang masuk") or teks.startswith("uang keluar"):
        is_masuk = teks.startswith("uang masuk")
        bagian_teks = teks.replace("uang masuk", "").replace("uang keluar", "")
        angka_saja = "".join([char for char in bagian_teks if char.isdigit()])
        
        if not angka_saja:
            await message.reply("❌ **Format salah, Kang!**\nContoh: `uang masuk 500.000` atau `uang keluar 50.000`")
            return
            
        nominal = int(angka_saja)
        waktu_sekarang = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        if is_masuk:
            data["masuk"] += nominal
            tipe = "🟢 UANG MASUK"
            keterangan = "Catatan pemasukan berhasil disimpan."
        else:
            data["keluar"] += nominal
            tipe = "🔴 UANG KELUAR"
            keterangan = "Catatan pengeluaran berhasil dipotong."
            
        saldo_total = data["masuk"] - data["keluar"]
        
        # 1. Simpan ke log jangka pendek DM (maksimal 5 saja)
        data["riwayat"].append(f"{tipe}: +{format_rupiah(nominal)}" if is_masuk else f"{tipe}: -{format_rupiah(nominal)}")
        if len(data["riwayat"]) > 5:
            data["riwayat"].pop(0)
            
        # 2. Simpan ke log permanen tak terbatas untuk dicetak ke PDF nanti
        data["riwayat_lengkap"].append({
            "waktu": waktu_sekarang,
            "tipe": "Pemasukan" if is_masuk else "Pengeluaran",
            "nominal": nominal
        })
        
        simpan_data(data)
        
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
        
    elif teks == "!keuangan":
        saldo_total = data["masuk"] - data["keluar"]
        embed = disnake.Embed(title="💳 TOTAL ISI BRANKAS SAAT INI", color=disnake.Color.blue())
        embed.add_field(name="📈 Total Pemasukan", value=format_rupiah(data["masuk"]), inline=True)
        embed.add_field(name="📉 Total Pengeluaran", value=format_rupiah(data["keluar"]), inline=True)
        embed.add_field(name="💰 TOTAL SALDO NETTO", value=f"**{format_rupiah(saldo_total)}**", inline=False)
        await message.reply(embed=embed)

    # 📌 FITUR TAMBAHAN: Akang bisa ketik !cetak-pdf kapan saja di DM jika ingin rekap instan tanpa nunggu 30 hari!
    elif teks == "!cetak-pdf":
        await message.reply("⏳ *Sedang merakit pembukuan PDF, mohon tunggu sebentar, Kang...*")
        nama_pdf = buat_pdf_laporan(data)
        await message.reply(
            f"✅ **Laporan Keuangan Instan Berhasil Dibuat!**",
            file=disnake.File(nama_pdf)
        )
        if os.path.exists(nama_pdf):
            os.remove(nama_pdf)
        
    elif teks == "!reset-keuangan":
        data = {"masuk": 0, "keluar": 0, "riwayat_lengkap": [], "riwayat": [], "terakhir_cetak": datetime.now().strftime("%Y-%m-%d")}
        simpan_data(data)
        await message.reply("🔄 **Buku kas pribadi berhasil dikosongkan kembali dari Rp 0!**")

    await bot.process_commands(message)

if TOKEN_BOT_KEUANGAN:
    bot.run(TOKEN_BOT_KEUANGAN)
else:
    print("❌ ERROR: Token tidak ditemukan di Variables Railway!")
