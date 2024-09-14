import uuid
from datetime import datetime

class Disco:
    def __init__(self, num_blocos=100, tamanho_bloco=10):
        self.tamanho_bloco = tamanho_bloco
        self.num_blocos = num_blocos
        self.blocos_dados = [None] * (num_blocos - 10)
        self.blocos_inodes = [None] * 10  

    def alocar_bloco_dados(self, dados):
        try:
            indice = self.blocos_dados.index(None)
        except ValueError:
            raise Exception("Sem blocos de dados disponíveis")
        
        self.blocos_dados[indice] = dados
        return indice

    def desalocar_bloco_dados(self, indice_bloco):
        if indice_bloco >= self.num_blocos:
            raise Exception("Índice de bloco de dados inválido")
        
        self.blocos_dados[indice_bloco] = None

    def alocar_bloco_inode(self, inode):
        try:
            indice = self.blocos_inodes.index(None)
        except ValueError:
            raise Exception("Sem blocos de inodes disponíveis")
        
        self.blocos_inodes[indice] = inode
        return indice

    def desalocar_bloco_inode(self, indice_bloco):
        if indice_bloco < 0 or indice_bloco >= len(self.blocos_inodes):
            raise Exception("Índice de bloco de inode inválido")
        
        self.blocos_inodes[indice_bloco] = None

    def obter_bloco_dados(self, indice_bloco):
        return self.blocos_dados[indice_bloco]

    def obter_bloco_inode(self, indice_bloco):
        return self.blocos_inodes[indice_bloco]

class Inode:
    def __init__(self, tipo_inode):
        self.id_inode = None
        self.tipo = tipo_inode
        self.criado_em = datetime.now()
        self.atualizado_em = datetime.now()
        self.blocos = []
        
    def __repr__(self):
        return f"Inode({self.id_inode}, tipo={self.tipo}, blocos={self.blocos})"

class Diretorio:
    def __init__(self):
        self.entradas = {}

    def adicionar_entrada(self, nome, inode):
        self.entradas[nome] = inode

    def remover_entrada(self, nome):
        if nome in self.entradas:
            del self.entradas[nome]

    def obter_inode(self, nome):
        return self.entradas.get(nome)

    def listar_entradas(self):
        return [(nome, inode) for nome, inode in self.entradas.items()]

class SistemaArquivos:
    def __init__(self):
        self.disco = Disco()
        self.inode_raiz = self.criar_inode('diretorio')

        self.raiz = Diretorio()

        indice_bloco = self.disco.alocar_bloco_dados(self.raiz)
        self.inode_raiz.blocos.append(indice_bloco)

        self.raiz.adicionar_entrada('.', self.inode_raiz)
        self.raiz.adicionar_entrada('..', self.inode_raiz)
        self.diretorio_atual = self.raiz

    def criar_inode(self, tipo_inode):
        inode = Inode(tipo_inode)
        inode.id_inode = self.disco.alocar_bloco_inode(inode)
        return inode

    def criar_arquivo(self, nome, dados=""):
        inode = self.criar_inode('arquivo')

        for i in range(0, len(dados), self.disco.tamanho_bloco):
            bloco_dados = dados[i:i + self.disco.tamanho_bloco]
            indice_bloco = self.disco.alocar_bloco_dados(bloco_dados)
            inode.blocos.append(indice_bloco)

        self.diretorio_atual.adicionar_entrada(nome, inode)
        print(f"Arquivo '{nome}' criado com inode {inode.id_inode} e {len(inode.blocos)} blocos de dados")

    def criar_diretorio(self, nome):
        inode_diretorio = self.criar_inode('diretorio')
        novo_diretorio = Diretorio()
        novo_diretorio.adicionar_entrada('.', inode_diretorio)
        novo_diretorio.adicionar_entrada('..', self.diretorio_atual.obter_inode('.'))
        self.diretorio_atual.adicionar_entrada(nome, inode_diretorio)

        indice_bloco = self.disco.alocar_bloco_dados(novo_diretorio)
        inode_diretorio.blocos.append(indice_bloco)

        print(f"Diretório '{nome}' criado com inode {inode_diretorio.id_inode}")

    def mudar_diretorio(self, nome):
        inode = self.diretorio_atual.obter_inode(nome)
        if inode and inode.tipo == 'diretorio':
            self.diretorio_atual = self.disco.obter_bloco_dados(inode.blocos[0])
            print(f"Entrou no diretório '{nome}'")
        else:
            print(f"Diretório '{nome}' não encontrado")

    def listar_diretorio(self):
        entradas = self.diretorio_atual.listar_entradas()
        print("Conteúdo do diretório:")
        for nome, inode in entradas:
            print(f"{nome} -> inode {inode.id_inode}")

    def exibir_conteudo_arquivo(self, nome):
        inode = self.diretorio_atual.obter_inode(nome)
        if inode and inode.tipo == 'arquivo':
            conteudo = ''.join([self.disco.obter_bloco_dados(indice) for indice in inode.blocos])
            print(f"Conteúdo do arquivo '{nome}': {conteudo}")
        else:
            print(f"Arquivo '{nome}' não encontrado")

    def escrever_arquivo(self, nome, dados):
        inode = self.diretorio_atual.obter_inode(nome)
        if inode and inode.tipo == 'arquivo':

            for indice_bloco in inode.blocos:
                self.disco.desalocar_bloco_dados(indice_bloco)

            inode.blocos = []

            for i in range(0, len(dados), self.disco.tamanho_bloco):
                bloco_dados = dados[i:i + self.disco.tamanho_bloco]
                indice_bloco = self.disco.alocar_bloco_dados(bloco_dados)
                inode.blocos.append(indice_bloco)

            inode.atualizado_em = datetime.now()

            print(f"Arquivo '{nome}' atualizado com {len(inode.blocos)} blocos de dados.")
        else:
            print(f"Arquivo '{nome}' não encontrado ou não é um arquivo válido.")

    def mover_arquivo(self, nome_arquivo, nome_diretorio_destino):

        inode_arquivo = self.diretorio_atual.obter_inode(nome_arquivo)
        if not inode_arquivo or inode_arquivo.tipo != 'arquivo':
            print(f"Arquivo '{nome_arquivo}' não encontrado no diretório atual.")
            return
        
        inode_destino = self.diretorio_atual.obter_inode(nome_diretorio_destino)
        if not inode_destino or inode_destino.tipo != 'diretorio':
            print(f"Diretório de destino '{nome_diretorio_destino}' não encontrado.")
            return
        
        self.diretorio_atual.remover_entrada(nome_arquivo)
        print(f"Arquivo '{nome_arquivo}' removido do diretório atual.")
        
        diretorio_destino = self.disco.obter_bloco_dados(inode_destino.blocos[0])
        diretorio_destino.adicionar_entrada(nome_arquivo, inode_arquivo)
        print(f"Arquivo '{nome_arquivo}' movido para o diretório '{nome_diretorio_destino}'.")

    def excluir_diretorio(self, nome):
        inode = self.diretorio_atual.obter_inode(nome)
        if inode and inode.tipo == 'diretorio':
            diretorio = self.disco.obter_bloco_dados(inode.blocos[0])

            for nome_entrada, inode_entrada in list(diretorio.entradas.items()):
                if nome_entrada in ['.', '..']:
                    continue
                
                self.mudar_diretorio(nome)
                if inode_entrada.tipo == 'arquivo':
                    self.excluir_arquivo(nome_entrada)
                elif inode_entrada.tipo == 'diretorio':
                    self.excluir_diretorio(nome_entrada)
                self.mudar_diretorio('..')

            for indice_bloco in inode.blocos:
                self.disco.desalocar_bloco_dados(indice_bloco)

            inode.blocos = []

            self.disco.desalocar_bloco_inode(inode.id_inode)

            self.diretorio_atual.remover_entrada(nome)

            print(f"Diretório '{nome}' excluído com sucesso.")
        else:
            print(f"Diretório '{nome}' não encontrado ou não é um diretório.")

    def excluir_arquivo(self, nome):
        inode = self.diretorio_atual.obter_inode(nome)
        self.listar_diretorio()
        if inode and inode.tipo == 'arquivo':
            for indice_bloco in inode.blocos:
                self.disco.desalocar_bloco_dados(indice_bloco)

            inode.blocos = []

            self.disco.desalocar_bloco_inode(inode.id_inode)

            self.diretorio_atual.remover_entrada(nome)

            print(f"Arquivo '{nome}' excluído com sucesso.")
        else:
            print(f"Arquivo '{nome}' não encontrado ou não é um arquivo.")


sistema = SistemaArquivos()
print(f"-------CRIAR ARQUIVOS E DIRETÓRIOS----------")
sistema.criar_arquivo("arquivo1.txt", "Conteúdo do arquivo 1")
sistema.criar_arquivo("arquivo2.txt", "Conteúdo do arquivo 2")
sistema.criar_diretorio("documentos")
sistema.listar_diretorio()

sistema.mudar_diretorio("documentos")
sistema.criar_arquivo("arquivo3.txt", "Arquivo 3 dentro de documentos")
sistema.listar_diretorio()

# print(f"Blocos de dados: {sistema.disco.blocos_dados}")
# print(f"Blocos de Inodes: {sistema.disco.blocos_inodes}")

print(f"-------EXIBIR CONTEÚDO DE ARQUIVOS----------")
sistema.exibir_conteudo_arquivo("arquivo3.txt")

print(f"-------MOVER ARQUIVO----------")
sistema.mudar_diretorio("..")
sistema.listar_diretorio() 
sistema.mover_arquivo("arquivo1.txt", "documentos")
sistema.listar_diretorio()
sistema.mudar_diretorio("documentos")
sistema.listar_diretorio()

print(f"-------ESCREVER NO ARQUIVO----------")
sistema.exibir_conteudo_arquivo("arquivo3.txt")
sistema.escrever_arquivo("arquivo3.txt", "Novo texto para o arquivo 3. Novo texto")
sistema.exibir_conteudo_arquivo("arquivo3.txt")

print(f"-------DELETAR DIRETÓRIO----------")
sistema.mudar_diretorio("..")
sistema.excluir_diretorio("documentos")
sistema.listar_diretorio()

print(f"-------DELETAR ARQUIVO----------")
sistema.mudar_diretorio("..")
sistema.excluir_arquivo("arquivo2.txt")
sistema.listar_diretorio()