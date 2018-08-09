# -*- coding: utf-8 -*-

#  efe_com_america.py
#  
#  Copyright 2018 Juan Manuel Dedionigis jmdedio@gmail.com
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  

import re
import urllib2
from urlparse import urljoin
from time import strftime
from xml.dom import minidom

class EfeComAmericaSpider():
    # Consulta la url y devuelve el contenido
    def consulta(self, url):
        hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
           'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
           'Accept-Encoding': 'none',
           'Accept-Language': 'en-US,en;q=0.8',
           'Connection': 'keep-alive'}

        try:
            req = urllib2.Request(url, headers = hdr)
            response = urllib2.urlopen(req)
            if response.getcode() == 200:
                return response.read()
        except Exception, e:
            print e
            print "Error URL %s" % (url)
    
    # Elimina las etiquetas html del contenido
    def limpiaetiquetas(self, item_texto):
        # Quita las etiquetas
        tag_re = re.compile(r'<[^>]+>')
        item_texto = tag_re.sub("", item_texto)
        # Quita los scrpts
        script_re = re.compile(r'<script[\s\S]+?>([\s\S]+?)</script>')
        item_texto = script_re.sub("", item_texto)
        return item_texto

    # Crea un fichero xml para cada entrada
    def xml(self, item):
        cdata = ['url', 'title', 'content', 'texto_img','volanta']
        doc = minidom.Document()
        root = doc.createElement("article")
        for clave_item, valor_item in item.iteritems():
            if clave_item in cdata and valor_item != '':
                dato_cdata = doc.createCDATASection(valor_item)
                cdv = doc.createElement(clave_item)
                cdv.appendChild(dato_cdata)
                root.appendChild(cdv)
                doc.appendChild(root)
            elif valor_item != '':
                dato_cdata = doc.createTextNode(valor_item)
                cdv = doc.createElement(clave_item)
                cdv.appendChild(dato_cdata)
                root.appendChild(cdv)
                doc.appendChild(root)
    
        fichero = item['url'][(item['url'].rfind('/') + 1):] + strftime("_%Y%m%d%H%M%S") + '.xml'
        doc.writexml( open(fichero, 'w'), indent = "  ", addindent = "  ", newl = '\n', encoding='iso-8859-1')
        doc.unlink()

    # Da formato a la fecha hora
    def formateafecha(self, fecha):
        if fecha:
            return ''.join(fecha).replace('-', '').replace('T', ' ')[:-1].split()
        else:
            return strftime("%Y%m%d"), strftime("%H:%M:%S")

    # Verifica si una entrada ya fue cargada
    # Utiliza la url
    def verifica(self, url):
        try:
            if url in open(log_carga, 'r').read():
                return True
            else:
                return False
        except:
            return False

    # Carga la url de la entrada en el log
    def carga(self, url):
        with open(log_carga, 'a') as fichero:
            fichero.write(url + '\n')
            fichero.close()

    # Extrae los enlaces de los artículos
    def extrae_enalces(self, url):
        html = self.consulta(url)
        hrefs1 = re.findall(r'<header><h3><a href="(.+?)"', html, re.I)
        hrefs2 = re.findall(r'<a href="(.+?)" itemprop="url">', html, re.I)
        return [urljoin('https://www.efe.com', href) for href in (hrefs1 + hrefs2)]

    # Extrae el contenido de cada artículo
    def extrae_contenido(self, url):
        html = self.consulta(url)
        item = {'url': '', 'date': '', 'time': '', 'title': '', 'content': '', 'texto_img': '', 'volanta': ''}
        item['url'] = url
        item['title'] = ''.join(re.findall('><meta property="og:title" content="(.+?)"', html))
        item['date'], item['time'] = self.formateafecha(re.findall('<time itemprop="dateModified" datetime="(.+?)"', html))
        item['volanta'] = ''.join(re.findall('itemprop="alternativeHeadline">(.+?)</div', html))
        item['texto_img'] = ''.join(re.findall(r'caption">(.+?)</', html))
        item['content'] = self.limpiaetiquetas(''.join(re.findall('itemprop="articleBody">([\S\s]+?[\S\s])</div>', html)))
        return item

if __name__ == "__main__":

    # Enlaces de cada sección
    enlaces = (
        'https://www.efe.com/efe/america/2',
        'https://www.efe.com/efe/america/mundo/20000012',
        'https://www.efe.com/efe/america/politica/20000035',
        'https://www.efe.com/efe/america/economia/20000011',
        'https://www.efe.com/efe/america/sociedad/20000013',
        'https://www.efe.com/efe/america/cultura/20000009',
        'https://www.efe.com/efe/america/deportes/20000010',
        'https://www.efe.com/efe/america/gente/20000014',
        'https://www.efe.com/efe/america/tecnologia/20000036',
        'https://www.efe.com/efe/america/reportajes/20000033',
        'https://www.efe.com/efe/america/comunicados/20004010',
        'https://www.efe.com/efe/america/infografias/20200130',
    )

    log_carga = 'efe.com_america.txt'
    spider = EfeComAmericaSpider()
    for enlace in enlaces:
        for entrada in spider.extrae_enalces(enlace):
            if not spider.verifica(entrada):
                spider.xml(spider.extrae_contenido(entrada))
                spider.carga(entrada)
