from telethon.sync import TelegramClient, events, utils
from telethon.events import StopPropagation
from telethon.tl import types
from telethon.sessions import StringSession
import requests
import re
import time
from datetime import datetime, timezone, timedelta
import asyncio
import os
import logging
from telethon.errors import FloodWaitError

logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)
api_id = 29052206
api_hash = "d50fc8079e72b4366c599cc64746612f"
bot_token = "5360496327:AAFxFp7Zs_lNNdD9orCl1BszONPeQPqFn-8"
bot_id = 567145327
users = [6130522435]
adm = [6130522435]

bot = TelegramClient("bot", api_id, api_hash).start(bot_token=bot_token)

gravador = []
def data_atual():
	return datetime.now(timezone(timedelta(hours=-3))).strftime("%d/%m/%Y , %H:%M")

def contar_gravacoes():
    return len(gravador)

numero_de_gravacoes = contar_gravacoes()

class Timer:
    def __init__(self, time_between=28):
        self.start_time = time.time()
        self.time_between = time_between

    def can_send(self):
        if time.time() > (self.start_time + self.time_between):
            self.start_time = time.time()
            return True
        return False

async def upload_telegram(arquivo, legenda, msg=None):
	try:
		msg=await msg.edit(f"{msg.text.replace('Screenshots','Upload...')}")
		proc = await asyncio.create_subprocess_shell(f"ffmpeg -ss 00:00:05 -i {arquivo} -frames:v 1 -q:v 2 {arquivo[:arquivo.find('.')]}_thumb.jpg",stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
		await proc.wait()
		timer=Timer()
		async def callback(current, total):
		   if timer.can_send():
		   	await msg.edit('{} {:.2%}'.format(msg.text, current / total))
		file=await bot.upload_file(f"{arquivo}", progress_callback=callback)
		thumb=await bot.upload_file(f"{arquivo[:arquivo.find('.')]}_thumb.jpg")
		shots=await bot.upload_file(f"{arquivo[:arquivo.find('.')]}.jpg") if os.path.isfile(f"{arquivo[:arquivo.find('.')]}.jpg")  else None
		attributes, mime_type = utils.get_attributes(f"{arquivo}")
		attributes[1].supports_streaming=True
		media=types.InputMediaUploadedDocument(
		file=file,
		mime_type=mime_type,
		attributes=attributes,
		thumb=thumb,
		force_file=False)
		envio=[media, shots] if shots!=None else media
		try:
			await bot.send_file(msg.chat_id, envio, caption = f"{legenda}", supports_streaming = True)
		except Exception as cu:
			print (cu)

		await asyncio.sleep(15)
		await msg.delete()
	except FloodWaitError as e:
	   	await asyncio.sleep(e.seconds)
	   	await upload_telegram(arquivo, legenda, msg)
	finally:

		if os.path.isfile(f"{arquivo}"):
			os.remove(f"{arquivo}")
		if os.path.isfile(f"{arquivo[:arquivo.find('.')]}.jpg"):
			os.remove(f"{arquivo[:arquivo.find('.')]}.jpg")
		if os.path.isfile(f"{arquivo[:arquivo.find('.')]}_thumb.jpg"):
			os.remove(f"{arquivo[:arquivo.find('.')]}_thumb.jpg")


async def thumb_video(arquivo, legenda, tipo_proc, msg=None):
	try:
		msg=await msg.edit(f"{msg.text.replace('Downloading...', 'Screenshots')}")
		proc = await asyncio.create_subprocess_shell(f"vcsi {arquivo} -w 850 -g 4x5 --quality 100 --metadata-position hidden --end-delay-percent 5 -o {arquivo[:arquivo.find('.')]}.jpg",stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
		stdout, stderr = await proc.communicate()
		print(f'[exited with {proc.returncode}]')
		if stdout:
		   print(f'[stdout]\n{stdout.decode()}')
		if stderr:
			print(f'[stderr]\n{stderr.decode()}')
		if proc.returncode==0:
			if tipo_proc=="gravador":
				await upload_telegram(arquivo, legenda, msg)
				return f"{arquivo[:arquivo.find('.')]}.jpg", msg
		else:
				if tipo_proc=="gravador":
					await upload_telegram(arquivo, legenda, msg)

	except FloodWaitError as e:
	   await asyncio.sleep(e.seconds)
	   await thumb_video(arquivo, legenda, tipo_proc, msg)


async def recorder_modelo(hls, legenda, msg=None, tipo_proc="gravador"):
    global gravador
    if hls in gravador:
        await msg.edit("🍌")
        return

    gravador.append(hls)
    data = f"{time.time()}".replace(".", "")
    arquivo = f'{data}_gravador.mp4'
    msg = await msg.edit(f"{msg.text.replace('🕹️', 'Downloading...')}")
    process=await asyncio.create_subprocess_shell(f"ffmpeg -headers 'referer: http-referrer=78373fa444d18cf962d99179d6621a64' -i {hls} -fs 1.8G -loglevel panic -c:v copy -c:a aac {arquivo}", shell=True)
    await process.wait()
    print(f'[exited with {process.returncode}]')
    if process.returncode == 0:
        if hls in gravador:
            gravador.remove(hls)
        await thumb_video(arquivo, legenda, "gravador", msg)
    else:
        if hls in gravador:
            gravador.remove(hls)
        await msg.edit("OFF")

loop=asyncio.get_event_loop()

@bot.on(events.NewMessage(chats=users,pattern=r"(.*)(\w+)(.flv)"))
async def recebe_link_m3u8(message):
    global gravador
    url_extract_pattern = "((?:http)\S+)"
    link = re.findall(url_extract_pattern, message.text)
    url = link[0]
    legenda_parte = re.search(r"/(\d+_sm_\w+)\.flv", url).group(1)
    legenda = f"{legenda_parte}\n{data_atual()}"
    msg = await message.reply("🕹️")
    loop.create_task(recorder_modelo(url, legenda, msg))

@bot.on(events.NewMessage(chats=adm,pattern='/status'))
async def status_gravacoes(event):
    numero_de_gravacoes = contar_gravacoes()
    await event.reply(f'downloading {numero_de_gravacoes} streaming.')

@bot.on(events.NewMessage(pattern='/rules'))
async def handle_rules(message):
    await message.reply("⛔ it is forbidden to record any link that contains child pornography.\nThe User who sends any such link will be banned without warning and his ID will be sent to telegram support for the necessary measures.\n⚠️ THE BAN WILL BE PERMANENT!!!")

@bot.on(events.NewMessage(pattern="/start"))
async def start_msg(message):
	await message.reply("Only Users Premium", parse_mode="html")

bot.run_until_disconnected()
