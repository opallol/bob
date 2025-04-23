const { default: makeWASocket, useMultiFileAuthState, DisconnectReason } = require('@whiskeysockets/baileys')
const axios = require('axios')
const qrcode = require('qrcode-terminal')
require('dotenv').config()

process.on('unhandledRejection', (reason) => {
  console.error('❌ Unhandled Rejection:', reason)
})

async function connectToWhatsApp() {
  try {
    const { state, saveCreds } = await useMultiFileAuthState('auth')

    const sock = makeWASocket({ auth: state, printQRInTerminal: false })
    sock.ev.on('creds.update', saveCreds)

    sock.ev.on('connection.update', ({ qr, connection, lastDisconnect }) => {
      if (qr) {
        console.log("📲 Scan QR code berikut untuk login:")
        qrcode.generate(qr, { small: true })
      }

      if (connection === 'close') {
        const shouldReconnect = lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut
        console.log('🔌 WA disconnected, reconnecting?', shouldReconnect)
        if (shouldReconnect) connectToWhatsApp()
      } else if (connection === 'open') {
        console.log('✅ WA Connected.')
      }
    })

    sock.ev.on('messages.upsert', async ({ messages }) => {
      try {
        if (!messages || messages.length === 0) return
        const msg = messages[0]
        if (msg.key.fromMe) return
        if (!msg.key.remoteJid.endsWith('@s.whatsapp.net')) return // hanya proses pesan dari user, bukan grup

        const sender = msg.key.remoteJid.split('@')[0]
        const content = msg.message
        let text = ""

        if (content.conversation) text = content.conversation
        else if (content.extendedTextMessage?.text) text = content.extendedTextMessage.text
        else if (content.imageMessage?.caption) text = content.imageMessage.caption
        else if (content.videoMessage?.caption) text = content.videoMessage.caption
        else text = "[Unsupported message type]"

        console.log(`📩 Pesan dari ${sender}: ${text}`)

        const allowedUsers = ['6289508592525', '6289611155155']
        if (!allowedUsers.includes(sender)) {
          console.log("📥 Pesan dari nomor lain (grup):", sender)

          const payload = {
            phone: sender,
            topik: "grup",
            isi: text
          }
          console.log("📨 Payload dikirim ke /teach:", JSON.stringify(payload, null, 2))

          try {
            const res = await axios.post(process.env.BACKEND_URL + '/teach', payload)
            console.log("✅ Respon dari /teach:", res.data)
          } catch (err) {
            console.error("❌ Gagal simpan memori grup:", err.response?.data || err.message)
          }

          return
        }

        if (!text || text.startsWith("[Unsupported")) {
          await sock.sendMessage(msg.key.remoteJid, { text: "Maaf, Bob belum bisa baca jenis pesan ini." })
          return
        }

        let reply = "Maaf, tidak ada balasan dari Bob."
        try {
          const res = await axios.post(process.env.BACKEND_URL + '/webhook', {
            message: text,
            phone: sender,
            kode_satker: sender === '6289508592525' ? '171298' : 'DEFAULT-SATKER'
          })

          reply = res.data.reply || reply

          // Kirim balasan teks
          await sock.sendMessage(msg.key.remoteJid, { text: reply })

          // Jika ada file suara (audio_url)
          if (res.data.audio_url) {
            const audioUrl = process.env.BACKEND_URL + '/' + res.data.audio_url
            await sock.sendMessage(msg.key.remoteJid, {
              audio: { url: audioUrl },
              mimetype: 'audio/mp4',
              ptt: true
            })
          }

        } catch (axiosErr) {
          console.error("❌ Gagal kirim ke backend:", axiosErr.response?.data || axiosErr.message)
          await sock.sendMessage(msg.key.remoteJid, { text: "Bob tidak bisa menghubungi backend 😢" })
        }

      } catch (err) {
        console.error("❌ Error handle message:", err.message)
        await sock.sendMessage(msg.key.remoteJid, { text: "Bob sedang error di backend 😢" })
      }
    })

  } catch (err) {
    console.error("❌ Gagal connectToWhatsApp:", err.message)
  }
}

connectToWhatsApp()