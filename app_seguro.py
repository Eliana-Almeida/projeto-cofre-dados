import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import csv
import json
import xml.etree.ElementTree as ET
from pathlib import Path
import hashlib
from cryptography.fernet import Fernet
from datetime import datetime


ARQUIVO_LOG = "auditoria.txt"
ARQUIVO_CHAVE = "chave.key"


def registrar_log(mensagem):
    data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(ARQUIVO_LOG, "a", encoding="utf-8") as log:
        log.write(f"[{data_hora}] {mensagem}\n")


def carregar_chave():
    if Path(ARQUIVO_CHAVE).exists():
        with open(ARQUIVO_CHAVE, "rb") as arquivo:
            return arquivo.read()

    chave = Fernet.generate_key()
    with open(ARQUIVO_CHAVE, "wb") as arquivo:
        arquivo.write(chave)
    return chave


class CofreDeDados:
    def __init__(self, janela):
        self.janela = janela
        self.janela.title("🔐 Cofre de Dados - SENAC")
        self.janela.geometry("1000x650")
        self.janela.configure(bg="#111827")

        self.arquivo_selecionado = None
        self.chave = carregar_chave()
        self.fernet = Fernet(self.chave)

        registrar_log("Sistema iniciado.")
        self.criar_interface()

    def criar_interface(self):
        titulo = tk.Label(
            self.janela,
            text="🔐 Cofre de Dados",
            font=("Arial", 24, "bold"),
            bg="#111827",
            fg="white"
        )
        titulo.pack(pady=15)

        subtitulo = tk.Label(
            self.janela,
            text="Auditoria, visualização e criptografia de arquivos confidenciais",
            font=("Arial", 12),
            bg="#111827",
            fg="#9CA3AF"
        )
        subtitulo.pack()

        frame_botoes = tk.Frame(self.janela, bg="#111827")
        frame_botoes.pack(pady=20)

        tk.Button(
            frame_botoes,
            text="Selecionar Arquivo",
            command=self.selecionar_arquivo,
            bg="#2563EB",
            fg="white",
            font=("Arial", 11, "bold"),
            width=20
        ).grid(row=0, column=0, padx=10)

        tk.Button(
            frame_botoes,
            text="Visualizar Conteúdo",
            command=self.visualizar_conteudo,
            bg="#16A34A",
            fg="white",
            font=("Arial", 11, "bold"),
            width=20
        ).grid(row=0, column=1, padx=10)

        tk.Button(
            frame_botoes,
            text="Copiar e Criptografar",
            command=self.criptografar_arquivo,
            bg="#DC2626",
            fg="white",
            font=("Arial", 11, "bold"),
            width=20
        ).grid(row=0, column=2, padx=10)

        self.label_arquivo = tk.Label(
            self.janela,
            text="Nenhum arquivo selecionado",
            bg="#111827",
            fg="#FBBF24",
            font=("Arial", 10)
        )
        self.label_arquivo.pack(pady=5)

        self.tabela = ttk.Treeview(self.janela)
        self.tabela.pack(fill="both", expand=True, padx=20, pady=10)

        self.log_tela = scrolledtext.ScrolledText(
            self.janela,
            height=8,
            bg="#020617",
            fg="#22C55E",
            font=("Consolas", 10)
        )
        self.log_tela.pack(fill="x", padx=20, pady=10)

        self.mostrar_log("Sistema iniciado com sucesso.")

    def mostrar_log(self, mensagem):
        data_hora = datetime.now().strftime("%H:%M:%S")
        self.log_tela.insert(tk.END, f"[{data_hora}] {mensagem}\n")
        self.log_tela.see(tk.END)

    def selecionar_arquivo(self):
        caminho = filedialog.askopenfilename(
            title="Selecione um arquivo",
            filetypes=[
                ("Arquivos suportados", "*.txt *.csv *.json *.xml"),
                ("TXT", "*.txt"),
                ("CSV", "*.csv"),
                ("JSON", "*.json"),
                ("XML", "*.xml")
            ]
        )

        if caminho:
            self.arquivo_selecionado = Path(caminho)
            self.label_arquivo.config(text=f"Arquivo: {self.arquivo_selecionado.name}")
            registrar_log(f"Arquivo selecionado: {self.arquivo_selecionado}")
            self.mostrar_log(f"Arquivo selecionado: {self.arquivo_selecionado.name}")

    def limpar_tabela(self):
        self.tabela.delete(*self.tabela.get_children())
        self.tabela["columns"] = ()
        self.tabela["show"] = "headings"

    def visualizar_conteudo(self):
        if not self.arquivo_selecionado:
            messagebox.showwarning("Atenção", "Selecione um arquivo primeiro.")
            return

        self.limpar_tabela()
        extensao = self.arquivo_selecionado.suffix.lower()

        try:
            if extensao == ".csv":
                self.ler_csv()
            elif extensao == ".json":
                self.ler_json()
            elif extensao == ".xml":
                self.ler_xml()
            elif extensao == ".txt":
                self.ler_txt()
            else:
                messagebox.showerror("Erro", "Tipo de arquivo não suportado.")
                return

            registrar_log(f"O arquivo {self.arquivo_selecionado.name} foi visualizado.")
            self.mostrar_log(f"Conteúdo visualizado: {self.arquivo_selecionado.name}")

        except Exception as erro:
            messagebox.showerror("Erro", f"Erro ao ler arquivo: {erro}")

    def ler_csv(self):
        with open(self.arquivo_selecionado, "r", encoding="utf-8") as arquivo:
            leitor = csv.reader(arquivo)
            linhas = list(leitor)

        if not linhas:
            return

        colunas = linhas[0]
        self.tabela["columns"] = colunas

        for coluna in colunas:
            self.tabela.heading(coluna, text=coluna)
            self.tabela.column(coluna, width=150)

        for linha in linhas[1:]:
            self.tabela.insert("", "end", values=linha)

    def ler_json(self):
        with open(self.arquivo_selecionado, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)

        if isinstance(dados, dict):
            dados = [dados]

        colunas = list(dados[0].keys())
        self.tabela["columns"] = colunas

        for coluna in colunas:
            self.tabela.heading(coluna, text=coluna)
            self.tabela.column(coluna, width=150)

        for item in dados:
            self.tabela.insert("", "end", values=[item.get(coluna, "") for coluna in colunas])

    def ler_xml(self):
        arvore = ET.parse(self.arquivo_selecionado)
        raiz = arvore.getroot()

        colunas = ["matricula", "nome", "setor", "nivel"]
        self.tabela["columns"] = colunas

        for coluna in colunas:
            self.tabela.heading(coluna, text=coluna)
            self.tabela.column(coluna, width=150)

        for funcionario in raiz.findall("funcionario"):
            matricula = funcionario.attrib.get("matricula", "")
            nome = funcionario.findtext("nome", "")
            setor = funcionario.findtext("setor", "")
            nivel = funcionario.findtext("nivel", "")

            self.tabela.insert("", "end", values=[matricula, nome, setor, nivel])

    def ler_txt(self):
        self.tabela["columns"] = ["linha", "conteudo"]
        self.tabela.heading("linha", text="Linha")
        self.tabela.heading("conteudo", text="Conteúdo")
        self.tabela.column("linha", width=80)
        self.tabela.column("conteudo", width=800)

        with open(self.arquivo_selecionado, "r", encoding="utf-8") as arquivo:
            for numero, linha in enumerate(arquivo, start=1):
                self.tabela.insert("", "end", values=[numero, linha.strip()])

    def gerar_hash(self):
        sha256 = hashlib.sha256()

        with open(self.arquivo_selecionado, "rb") as arquivo:
            for bloco in iter(lambda: arquivo.read(4096), b""):
                sha256.update(bloco)

        return sha256.hexdigest()

    def criptografar_arquivo(self):
        if not self.arquivo_selecionado:
            messagebox.showwarning("Atenção", "Selecione um arquivo primeiro.")
            return

        pasta_destino = filedialog.askdirectory(title="Escolha a pasta de destino")

        if not pasta_destino:
            return

        pasta_destino = Path(pasta_destino)
        hash_arquivo = self.gerar_hash()

        with open(self.arquivo_selecionado, "rb") as arquivo:
            conteudo = arquivo.read()

        conteudo_criptografado = self.fernet.encrypt(conteudo)

        arquivo_enc = pasta_destino / f"{self.arquivo_selecionado.name}.enc"
        arquivo_hash = pasta_destino / f"{self.arquivo_selecionado.name}.hash.txt"

        with open(arquivo_enc, "wb") as arquivo:
            arquivo.write(conteudo_criptografado)

        with open(arquivo_hash, "w", encoding="utf-8") as arquivo:
            arquivo.write(f"Arquivo original: {self.arquivo_selecionado.name}\n")
            arquivo.write(f"Hash SHA-256: {hash_arquivo}\n")

        registrar_log(
            f"Arquivo copiado e criptografado de {self.arquivo_selecionado} para {arquivo_enc}. Hash: {hash_arquivo}"
        )

        self.mostrar_log("Arquivo criptografado com sucesso.")
        self.mostrar_log(f"Arquivo .enc salvo em: {arquivo_enc}")
        self.mostrar_log(f"Hash salvo em: {arquivo_hash}")

        messagebox.showinfo("Sucesso", "Arquivo criptografado e hash gerado com sucesso!")


if __name__ == "__main__":
    janela = tk.Tk()
    app = CofreDeDados(janela)
    janela.mainloop()