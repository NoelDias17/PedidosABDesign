import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication

from flask import Flask, request, render_template

import random
import string

import os

from PIL import Image, ImageDraw
import io

app = Flask(__name__)

def enviar_email(destinatario, assunto, mensagem, imagem_cores, anexos=None):  
    # Configurações do servidor SMTP do Gmail
    email_remetente = "suporteabelairadesign@gmail.com"
    senha = "kfldfkxrvhraogsf"  # gmail - gerenciar conta - segurança - verificação 2 etapas - senhas de app - gerar
    servidor_smtp = "smtp.gmail.com"
    porta = 587

    # Cria o objeto de conexão SMTP
    smtp = smtplib.SMTP(servidor_smtp, porta)
    smtp.starttls()
    smtp.login(email_remetente, senha)

    # Cria o e-mail
    msg = MIMEMultipart()
    msg['From'] = email_remetente
    msg['To'] = destinatario
    msg['Subject'] = assunto
    corpo = mensagem
    msg.attach(MIMEText(corpo, "html"))

    if anexos:
        for anexo in anexos:
            with open(anexo, "rb") as f:
                anexo_part = MIMEApplication(f.read())
            anexo_part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(anexo)}")
            msg.attach(anexo_part)

    with open(imagem_cores, "rb") as image_file:
        msg_image = MIMEImage(image_file.read())
    msg_image.add_header("Content-ID", "<image1>")
    msg.attach(msg_image)

    # Envia o e-mail
    smtp.sendmail(email_remetente, destinatario, msg.as_string())
    smtp.quit()

def compactar_imagem(imagem, qualidade=85):
    img = Image.open(imagem)
    formato_original = img.format.lower()
    output = io.BytesIO()
    img.save(output, format=formato_original, quality=qualidade)
    output.seek(0)
    return output
    
@app.route('/',  methods=['GET', 'POST']) 
def formulario():
    if request.method == 'POST':
        # Captura os dados do formulário
        nome_cliente = request.form.get('nome_cliente')
        email_cliente = request.form.get('email_cliente')
        tema_personalizado = request.form.get('tema_personalizado')
        nome_personalizado = request.form.get('nome_personalizado')
        idade_personalizado = request.form.get('idade')
        if idade_personalizado == "":
            idade_personalizado = "Não Mencionada"
        acabamento = request.form.get('acabamento')
        cores_principais = request.form.getlist('cores_principais[]')
        rgb_colors = [tuple(int(cor_principal[i:i+2], 16) for i in (1, 3, 5)) for cor_principal in cores_principais]
        
        # Criando Quadrado
        square_size = 50
        border_width = 1
        image_width = square_size * len(rgb_colors)
        image = Image.new("RGB", (image_width, square_size), "white")
        draw = ImageDraw.Draw(image)

        for i, color in enumerate(rgb_colors):
            left = i * square_size
            right = (i + 1) * square_size
            draw.rectangle(
                [(left, 0), (right - 1, square_size - 1)],
                fill=color,
                outline="black",
                width=border_width
            )

        #Salvando arquivo temporário
        temp_image_path = "temp/colored_squares.png"
        image.save(temp_image_path)
        
        # Pegando detalhes e obs
        detalhes_observacoes = request.form.get('detalhes_observacoes')
        if detalhes_observacoes == "":
            detalhes_observacoes = "-"

        # Captura as imagens das referências personalizadas
        referencias_personalizados1 = request.files.get('referencias_personalizados1')
        referencias_personalizados2 = request.files.get('referencias_personalizados2')
        referencias_personalizados3 = request.files.get('referencias_personalizados3')

        caminhos_referencias_personalizados = []

        for idx, foto_referencia in enumerate([referencias_personalizados1, referencias_personalizados2, referencias_personalizados3], start=1):
            if foto_referencia:
                caminho_foto_referencia = f"temp/{idx}_{foto_referencia.filename}"  # Substitua pelo caminho correto
                foto_referencia.save(caminho_foto_referencia)

                # Compacta a imagem
                imagem_compactada = compactar_imagem(caminho_foto_referencia, qualidade=10)
                caminho_temporario = f"temp/Imagem_Referencia_{idx}.png" # referencia_{idx}_compactada
                with open(caminho_temporario, "wb") as f:
                    f.write(imagem_compactada.read())
                caminhos_referencias_personalizados.append(caminho_temporario)

                os.remove(caminho_foto_referencia)


        foto_painel = request.files.get('foto_painel')
        
        caminho_foto_painel = None
        caminho_temporario_painel = None

        if foto_painel:
            caminho_foto_painel = f"temp/{foto_painel.filename}"  # Substitua pelo caminho correto
            foto_painel.save(caminho_foto_painel)

            # Compacta a imagem
            imagem_compactada = compactar_imagem(caminho_foto_painel, qualidade=10)
            caminho_temporario_painel = f"temp/Imagem do Painel.png"
            with open(caminho_temporario_painel, "wb") as f:
                f.write(imagem_compactada.read())

            os.remove(caminho_foto_painel)

        def generate_ticket(length=10): # 0.00000000000016% de chances do ticket se repetir
            characters = string.ascii_letters + string.digits  # Letras maiúsculas, minúsculas e números
            ticket = ''.join(random.choice(characters) for _ in range(length))
            return ticket
        
        ticket_pedido = generate_ticket()
        
        # Envio do e-mail para a empresa
        assunto_empresa = f"Novo Pedido de {nome_cliente} - {ticket_pedido}"
        # mensagem_empresa = f"Atenção, Chegou um novo pedido de personalizado!\n\nDetalhes do pedido\n\nTicket: {ticket_pedido}\nNome do Cliente: {nome_cliente}\nEmail do Cliente: {email_cliente}\nTema do Personalizado: {tema_personalizado}\nNome Personalizado: {nome_personalizado}\nIdade Personalizado: {idade_personalizado}\nAcabamento: {acabamento}\nCódigo HEX das Cores Principais: {', '.join(cores_principais)}\nDetalhes e Observações: {detalhes_observacoes}\n\nMãos à obra!"
        # print(f"Atenção, Chegou um novo pedido de personalizado!\n\nDetalhes do pedido\n\nTicket: {ticket_pedido}\nNome do Cliente: {nome_cliente}\nEmail do Cliente: {email_cliente}\nNome Personalizado: {nome_personalizado}\nIdade Personalizado: {idade_personalizado}\nAcabamento: {acabamento}\nCores Principais: {', '.join(cores_principais)}\nDetalhes e Observações: {detalhes_observacoes}")

        mensagem_empresa = f"""
<html>
<head></head>
<body>
<p>Atenção, Chegou um novo pedido de personalizado!</p>
<p><strong>--------- Detalhes do pedido ---------</strong></p>
<p><strong>Ticket:</strong> {ticket_pedido}</p>
<p><strong>Nome do Cliente:</strong> {nome_cliente}</p>
<p><strong>Email do Cliente:</strong> {email_cliente}</p>
<p><strong>Tema do Personalizado:</strong> {tema_personalizado}</p>
<p><strong>Nome Personalizado:</strong> {nome_personalizado}</p>
<p><strong>Idade Personalizado:</strong> {idade_personalizado}</p>
<p><strong>Acabamento:</strong> {acabamento}</p>
<p><strong>Cores Escolhidas:</strong></p>
<img src="cid:image1">
<p><strong>Detalhes e Observações:</strong> {detalhes_observacoes}</p>
<p>Mãos à obra!</p>
</body>
</html>
        """

        # Verifica se há imagens de referência para enviar como anexos

        if caminho_temporario_painel and caminhos_referencias_personalizados:
            anexos_empresa = [caminho_temporario_painel] + caminhos_referencias_personalizados
        elif caminho_temporario_painel:
            anexos_empresa = [caminho_temporario_painel]
        elif caminhos_referencias_personalizados:
            anexos_empresa = caminhos_referencias_personalizados
        else:
            anexos_empresa = None
        
        # anexos_empresa = [caminho_temporario_painel] + caminhos_referencias_personalizados if caminho_temporario_painel or caminhos_referencias_personalizados else None
        enviar_email('suporteabelairadesign@gmail.com',assunto_empresa, mensagem_empresa,imagem_cores=temp_image_path, anexos=anexos_empresa)

        # Envio do e-mail de confirmação para o cliente
        assunto_cliente = f"Olá {nome_cliente}, Recebemos seu Pedido! - Abelaira Design"
        # mensagem_cliente = f"Olá {nome_cliente},\nSeu pedido foi recebido com sucesso!\n\nDetalhes do Pedido\n\nTicket: {ticket_pedido}\nTema do Personalizado: {tema_personalizado}\nNome Personalizado: {nome_personalizado}\nIdade Personalizado: {idade_personalizado}\nAcabamento: {acabamento}\nCódigo HEX das Cores Principais: {', '.join(cores_principais)}\nDetalhes e Observações: {detalhes_observacoes}\n\nAguarde nosso suporte entrar em contato com você para mais informações.\nObrigado por escolher a Abelaira Design Personalizados!"
        # print(f"Olá {nome_cliente},\n\nSeu pedido foi recebido com sucesso!\n\nDetalhes do Pedido\n\nTicket: {ticket_pedido}\nNome Personalizado: {nome_personalizado}\nAcabamento: {acabamento}\nCores Principais: {', '.join(cores_principais)}\nDetalhes e Observações: {detalhes_observacoes}\n\nAguarde nosso suporte entrar em contato com você para mais informações.\nObrigado por escolher a Abelaira Design!")
        mensagem_cliente = f"""
<html>
<head></head>
<body>
<p>Olá {nome_cliente},</p>
<p><strong>--------- Detalhes do seu pedido ---------</strong></p>
<p><strong>Ticket:</strong> {ticket_pedido}</p>
<p><strong>Tema do Personalizado:</strong> {tema_personalizado}</p>
<p><strong>Nome Personalizado:</strong> {nome_personalizado}</p>
<p><strong>Idade Personalizado:</strong> {idade_personalizado}</p>
<p><strong>Acabamento:</strong> {acabamento}</p>
<p><strong>Cores Escolhidas:</strong></p>
<img src="cid:image1">
<p><strong>Detalhes e Observações:</strong> {detalhes_observacoes}</p><br>
<p>Aguarde nosso suporte entrar em contato com você para mais informações.</p>
<p>Obrigado por escolher a Abelaira Design Personalizados!</p>
</body>
</html>
        """
        
        enviar_email(email_cliente, assunto_cliente, mensagem_cliente, temp_image_path)

        # print(nome_cliente, email_cliente, idade_personalizado, nome_personalizado, acabamento, cores_principais, detalhes_observacoes)
        
        for caminho_temporario in caminhos_referencias_personalizados:
            os.remove(caminho_temporario)
        
        try:
            os.remove(caminho_temporario_painel)
        except:
            pass

        try:
            os.remove(temp_image_path)
        except:
            pass

        return render_template("pedido_enviado.html")
    return render_template("index.html")

if __name__ == '__main__':
    app.run(debug=True)
