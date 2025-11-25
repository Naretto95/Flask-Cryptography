#!/usr/bin/python
# coding=utf8

def vers_8bit(c: str) -> str:
    chaine_binaire = bin(ord(c))[2:]
    return "0" * (8 - len(chaine_binaire)) + chaine_binaire

def modifier_pixel(pixel: tuple, bit: str) -> tuple:
    r_val = pixel[0]
    rep_binaire = bin(r_val)[2:]
    rep_bin_mod = rep_binaire[:-1] + bit
    r_val = int(rep_bin_mod, 2)
    return (r_val,) + pixel[1:]

def recuperer_bit_pfaible(pixel: tuple) -> str:
    r_val = pixel[0]
    return bin(r_val)[-1]

def cacher(image, message: str):
    dimX, dimY = image.size
    im = image.load()
    message_binaire = ''.join([vers_8bit(c) for c in message])
    posx_pixel = 0
    posy_pixel = 0
    for bit in message_binaire:
        im[posx_pixel, posy_pixel] = modifier_pixel(im[posx_pixel, posy_pixel], bit)
        posx_pixel += 1
        if posx_pixel == dimX:
            posx_pixel = 0
            posy_pixel += 1
        if posy_pixel >= dimY:
            raise ValueError("Message too long for image")

def recuperer(image, taille: int) -> str:
    message = ""
    dimX, dimY = image.size
    im = image.load()
    posx_pixel = 0
    posy_pixel = 0
    for _ in range(taille):
        rep_binaire = ""
        for _ in range(8):
            rep_binaire += recuperer_bit_pfaible(im[posx_pixel, posy_pixel])
            posx_pixel += 1
            if posx_pixel == dimX:
                posx_pixel = 0
                posy_pixel += 1
        message += chr(int(rep_binaire, 2))
    return message
