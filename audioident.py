#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import os
import sqlite3
from hashlib import md5
import sys

def get_args():
    '''Função que analisae os arqumentos recebidos em linha do comando.'''
    parser = argparse.ArgumentParser(
        description="Identifica arquivos em caminho informado.",
        epilog="%(prog)s -d CAMINHO1 CAMINHO2",

        add_help=False,
    )
    parser.add_argument('-h','--help', action='help', 
        default=argparse.SUPPRESS, help='Mostra esta\
        mensagem e encerra.')
    parser.add_argument('-d', '--diretorio', nargs='+', 
        help='Especifica caminho em que serão pesquisados os arquivos.',
        required=True)
    parser.add_argument('-b', '--banco', default='./ai.db',
        help='Especifica database de áudios.')

    parser.add_argument('-s', '--saida', choices=['csv', 'stdout' ],
        default='csv', help='Especifica qual saída deve ser utilizada para\
        relatório de áudios. Padrão: csv e stderr para áudios não\
        identificados.')

    return parser.parse_args()

def load_data(database: str) -> dict:
    '''Função que carrega dados do banco sqlite, recebido no parâmetro
    database e retorna um dicionário.'''

    if not os.path.isfile(database):
        raise FileNotFoundError

    if not os.access(database, os.R_OK):
        raise PermissionError

    db = sqlite3.connect(database)
    c = db.cursor()

    d = {}
    for r in c.execute("SELECT checksum, texto FROM audios").fetchall():
        d[r[0]] = r[1]

    return d

def ident_data(database: dict, caminho: str) -> dict:
    '''Pesquisa em caminho e checa se os áudios existem no dicionário em caso
    positivo, preenche dicionário de retorno com o caminho completo do arquivo
    e a transcrição do áudio. Em caso negativo preenche stderr com informação
    sobre o áudio desconhecido.'''
    r = {}
    if sys.version_info < (3, 5):
        pesquisa = old_pesquisa
    else:
        from glob import iglob as pesquisa

    for pasta in caminho:
        for filename in pesquisa('{}/**/*.gsm'.format(pasta), recursive=True):
            chk = arqhash(os.path.abspath(filename))
            if chk in database:
                r[os.path.abspath(filename)] = database[chk]
            else:
                print('DESCONHECIDO [{}]({})'.format(os.path.abspath(filename),chk),
                file=sys.stderr)
    return r

def old_pesquisa(caminho: str, recursive=True):
    '''Pesquisa recursivamente em caminho os arquivos e retorna em uma lista.
    Função criada somente para atender versões do python3 inferiores a 3.5'''
    import fnmatch

    caminho = caminho.split('/*',1)[0]
    for root, dirnames, filenames in os.walk(caminho):
        for filename in fnmatch.filter(filenames, '*.gsm'):
            yield os.path.join(root, filename)

def arqhash(arquivo: str) -> str:
    '''Retorna o hash md5 de [arquivo].'''
    with open(arquivo, 'rb') as arq:
        return md5(arq.read()).hexdigest()

def saida_padrao(data: dict):
    '''Recebe dicionário e exibe saída em tela no formato: [chave] valor.'''
    for chave, valor in data.items():
        print('[{}]  {}'.format(chave, valor))

def saida_csv(data: dict):
    '''Recebe dicionário simples e direciona a saída para arquivo csv.'''
    import csv

    with open('summary.csv','w',encoding='utf-8') as csvdata:
        fieldnames = [ 'arquivo', 'texto' ]
        writer = csv.writer(csvdata)

        for chave in sorted(data.keys()):
            writer.writerow([ chave, data[chave] ])

saida = {
    'csv' : saida_csv,
    'stdout' : saida_padrao,
}

if __name__ == "__main__":
    opts = get_args()
    db = load_data(opts.banco)
    saida[opts.saida](ident_data(db, opts.diretorio))

# vim: sw=4 ts=4 sm et fo+=t tw=79 fileencoding=utf-8 cursorline
