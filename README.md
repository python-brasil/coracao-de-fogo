# Coração de fogo em Tkinter

Uma estrelinha percorre o contorno do coração soltando fogo e faíscas e
deixa um rastro de brasas. Quando o contorno fecha, o fogo sobe da ponta e o
coração inteiro queima. Só `tkinter`, `math` e `random`.

```
python coracao_fogo.py             # anima na janela
python coracao_fogo.py --gravar    # grava coracao_fogo.mp4 (precisa de pillow + ffmpeg)
```

Como funciona:

1. **A curva** é a paramétrica do coração (`x = 16·sen³t`, `y = 13·cos t − …`).
   `t = 0` é o vinco de cima; a estrelinha desce pela direita, passa pela
   ponta e volta pela esquerda em 6 s.
2. **Partículas** são ovais e linhas do canvas com posição, velocidade, tamanho
   e vida. A cada quadro envelhecem, sobem, encolhem e trocam de cor.
3. **Transparência que o Tkinter não tem**: `blend(cor, alpha)` mistura a cor
   com o fundo. É o que faz o fogo apagar e as brasas cintilarem.
4. **A cor do fogo** vem de uma rampa contínua (branco, amarelo, laranja,
   vermelho, escuro) pela idade da partícula, não de três faixas fixas.
5. **O incêndio** usa uma frente que sobe da ponta ao topo: toda brasa e todo
   ponto do miolo abaixo da frente vira um foco de chamas.

`fx.py` é o laboratório de onde a partícula saiu: fogo, faíscas, chuva e neve
com as teclas 1 a 4.

Publicado pelo [@python_brasil](https://instagram.com/python_brasil).
