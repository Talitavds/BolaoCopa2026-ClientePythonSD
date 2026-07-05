import tkinter as tk
import customtkinter as ctk
import requests
import threading
from datetime import datetime

# Configurações globais de design do CustomTkinter
ctk.set_appearance_mode("Dark")  # Opções: "System", "Dark", "Light"
ctk.set_default_color_theme("blue")  # Opções: "blue", "green", "dark-blue"

BASE_URL = "http://bolao.breskovit.cloud:8080"
CLIENT_ID = "cliente-python"

class BolaoApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configuração da janela principal
        self.title("🏆 Bolão Copa 2026")
        self.geometry("750x600")
        self.minsize(650, 500)

        # Estado interno da aplicação
        self.current_match = None
        self.selected_match_id = None
        self.all_matches = []
        self.sent_guesses = {}  # Guarda palpites enviados nesta sessão: {match_id: (score_a, score_b)}

        # Layout da UI
        self.criar_interface()

        # Carregar dados iniciais em segundo plano para não congelar o ecrã
        self.carregar_dados_iniciais()

    def criar_interface(self):
        """Constrói a estrutura de abas e componentes visuais."""
        # Título Superior
        self.label_titulo = ctk.CTkLabel(
            self, text="🏆 BOLÃO COPA 2026", font=ctk.CTkFont(size=24, weight="bold")
        )
        self.label_titulo.pack(pady=15)

        # Área do Utilizador (Username unificado para todas as operações)
        self.frame_user = ctk.CTkFrame(self)
        self.frame_user.pack(fill="x", padx=20, pady=5)
        
        self.label_username = ctk.CTkLabel(
            self.frame_user, text="Username do Jogador:", font=ctk.CTkFont(weight="bold")
        )
        self.label_username.pack(side="left", padx=10, pady=10)
        
        self.entry_username = ctk.CTkEntry(
            self.frame_user, placeholder_text="Ex: joao_silva", width=200
        )
        self.entry_username.pack(side="left", padx=10, pady=10)
        self.entry_username.insert(0, "jogador_anonimo")  # Valor padrão amigável

        # Criação das Abas de navegação
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=10)

        self.tab_palpite = self.tabview.add("⚽ Fazer Palpite")
       # self.tab_partidas = self.tabview.add("📅 Calendário")
        self.tab_ranking = self.tabview.add("📊 Classificação")

        # Configurar cada aba individualmente
        self.configurar_aba_palpite()
       # self.configurar_aba_partidas()
        self.configurar_aba_ranking()

    # --- ABA 1: PALPITE ---
    def configurar_aba_palpite(self):
        # Cabeçalho com botão de atualizar (mesmo padrão da aba de Ranking)
        self.frame_header_palpite = ctk.CTkFrame(self.tab_palpite, fg_color="transparent")
        self.frame_header_palpite.pack(fill="x", padx=10, pady=(10, 0))

        self.btn_refresh_palpite = ctk.CTkButton(
            self.frame_header_palpite, text="🔄 Atualizar Partida", width=140,
            command=self.acao_atualizar_partida
        )
        self.btn_refresh_palpite.pack(side="right")

        # Frame central do Palpite
        self.frame_palpite_card = ctk.CTkFrame(self.tab_palpite)
        self.frame_palpite_card.pack(pady=20, padx=40, fill="both", expand=True)

        self.label_status_jogo = ctk.CTkLabel(
            self.frame_palpite_card, text="A CARREGAR PARTIDA ATUAL...", 
            font=ctk.CTkFont(size=12, weight="bold"), text_color="gray"
        )
        self.label_status_jogo.pack(pady=10)

        # Área de confronto dos Equipas
        self.frame_versus = ctk.CTkFrame(self.frame_palpite_card, fg_color="transparent")
        self.frame_versus.pack(pady=15)

        # Equipa A
        self.label_team_a = ctk.CTkLabel(
            self.frame_versus, text="Equipe A", font=ctk.CTkFont(size=18, weight="bold")
        )
        self.label_team_a.grid(row=0, column=0, padx=20)
        
        self.entry_score_a = ctk.CTkEntry(self.frame_versus, width=60, font=ctk.CTkFont(size=20), justify="center")
        self.entry_score_a.grid(row=0, column=1, padx=10)

        # Divisor "VS"
        self.label_vs = ctk.CTkLabel(self.frame_versus, text="X", font=ctk.CTkFont(size=18, weight="bold"))
        self.label_vs.grid(row=0, column=2, padx=10)

        # Equipa B
        self.entry_score_b = ctk.CTkEntry(self.frame_versus, width=60, font=ctk.CTkFont(size=20), justify="center")
        self.entry_score_b.grid(row=0, column=3, padx=10)

        self.label_team_b = ctk.CTkLabel(
            self.frame_versus, text="Equipe B", font=ctk.CTkFont(size=18, weight="bold")
        )
        self.label_team_b.grid(row=0, column=4, padx=20)

        # Data do Jogo
        self.label_kickoff = ctk.CTkLabel(self.frame_palpite_card, text="", font=ctk.CTkFont(slant="italic"))
        self.label_kickoff.pack(pady=5)

        # Aviso de palpite pré-existente localmente
        self.label_aviso_palpite = ctk.CTkLabel(self.frame_palpite_card, text="", text_color="#ffb86c")
        self.label_aviso_palpite.pack(pady=5)

        # Botão de Envio
        self.btn_enviar_palpite = ctk.CTkButton(
            self.frame_palpite_card, text="Submeter Palpite", 
            command=self.acao_submeter_palpite, font=ctk.CTkFont(weight="bold")
        )
        self.btn_enviar_palpite.pack(pady=20)

        # Mensagem de Feedback de Operação
        self.label_feedback = ctk.CTkLabel(self.frame_palpite_card, text="")
        self.label_feedback.pack(pady=5)

    # --- ABA 2: RANKING ---
    def configurar_aba_ranking(self):
        self.frame_header_ranking = ctk.CTkFrame(self.tab_ranking, fg_color="transparent")
        self.frame_header_ranking.pack(fill="x", padx=10, pady=5)

        self.label_ranking_info = ctk.CTkLabel(
            self.frame_header_ranking, text="Pontuação: Placar exato = 10pts | Acertou vencedor/empate = 5pts | Erro = 0pts",
            font=ctk.CTkFont(size=11, slant="italic")
        )
        self.label_ranking_info.pack(side="left")

        self.btn_refresh_ranking = ctk.CTkButton(
            self.frame_header_ranking, text="🔄 Atualizar Ranking", width=120, command=self.carregar_ranking
        )
        self.btn_refresh_ranking.pack(side="right")

        # Scroll para tabela de classificação
        self.scroll_ranking = ctk.CTkScrollableFrame(self.tab_ranking)
        self.scroll_ranking.pack(fill="both", expand=True, padx=10, pady=10)

    # --- LÓGICA DE API & THREADS ---

    def carregar_dados_iniciais(self):
        """Inicia threads para carregar todos os dados de forma assíncrona."""
        threading.Thread(target=self.carregar_partida_atual, daemon=True).start()
        threading.Thread(target=self.carregar_ranking, daemon=True).start()

    def acao_atualizar_partida(self):
        """Dispara a atualização da partida atual numa thread separada (chamado pelo botão)."""
        threading.Thread(target=self.carregar_partida_atual, daemon=True).start()

    def carregar_partida_atual(self):
        """Busca o jogo ativo a decorrer (ou último encerrado)."""
        try:
            self.btn_refresh_palpite.configure(state="disabled", text="A carregar...")
            url = f"{BASE_URL}/api/"
            headers = {"X-Client-Id": CLIENT_ID}
            response = requests.get(url, headers=headers, timeout=5)

            if response.status_code == 200:
                match_data = response.json()
                self.atualizar_visual_palpite(match_data)
            else:
                self.label_status_jogo.configure(text="Nenhuma partida ativa encontrada no momento.", text_color="red")
            self.btn_refresh_palpite.configure(state="normal", text="🔄 Atualizar Partida")
        except Exception as e:
            self.label_status_jogo.configure(text=f"Erro de ligação à rede.", text_color="red")
            self.btn_refresh_palpite.configure(state="normal", text="🔄 Erro ao carregar")

    def carregar_ranking(self):
        """Carrega a classificação geral dos utilizadores."""
        try:
            self.btn_refresh_ranking.configure(state="disabled", text="A carregar...")
            url = f"{BASE_URL}/api/ranking"
            headers = {"X-Client-Id": CLIENT_ID}
            response = requests.get(url, headers=headers, timeout=5)

            if response.status_code == 200:
                ranking_data = response.json()
                self.desenhar_ranking(ranking_data)
            self.btn_refresh_ranking.configure(state="normal", text="🔄 Atualizar Ranking")
        except Exception:
            self.btn_refresh_ranking.configure(state="normal", text="🔄 Erro ao carregar")

    # --- MANIPULAÇÃO VISUAL DA UI ---

    def atualizar_visual_palpite(self, match_data):
        """Desenha a partida selecionada na aba de apostas."""
        self.current_match = match_data
        self.selected_match_id = match_data.get("id")

        # Tratamento de Nomes e Bandeiras
        team_a_name = match_data["team_a"].get("name", "Equipa A")
        team_a_flag = match_data["team_a"].get("flag", "")
        team_b_name = match_data["team_b"].get("name", "Equipa B")
        team_b_flag = match_data["team_b"].get("flag", "")

        self.label_team_a.configure(text=f"{team_a_flag} {team_a_name}".strip())
        self.label_team_b.configure(text=f"{team_b_name} {team_b_flag}".strip())

        # Formatação de Data
        kickoff_str = match_data.get("kickoff_at", "")
        try:
            dt = datetime.fromisoformat(kickoff_str.replace("Z", "+00:00"))
            data_formatada = dt.strftime("%d/%m/%Y às %H:%M (UTC)")
        except ValueError:
            data_formatada = kickoff_str

        self.label_kickoff.configure(text=f"Início: {data_formatada}")

        status = match_data.get("status", "scheduled")
        if status == "finished":
            # Jogo já terminou. Bloqueia a aposta
            real_score = match_data.get("real_score", {})
            real_a = real_score.get("a", "-")
            real_b = real_score.get("b", "-")
            
            self.label_status_jogo.configure(
                text=f"PARTIDA TERMINADA (Placar Real: {real_a} - {real_b})",
                text_color="#ff5555"
            )
            self.entry_score_a.configure(state="disabled")
            self.entry_score_b.configure(state="disabled")
            self.btn_enviar_palpite.configure(state="disabled", text="Apostas Encerradas")
            self.label_aviso_palpite.configure(text="Não é possível palpitar em partidas concluídas.", text_color="#ff5555")
        else:
            # Jogo está agendado e aberto a palpites
            self.label_status_jogo.configure(text="🔥 APOSTAS ABERTAS PARA ESTA PARTIDA!", text_color="#55ff55")
            self.entry_score_a.configure(state="normal")
            self.entry_score_b.configure(state="normal")
            
            # Limpa campos ou coloca valor pré-existente enviado nesta sessão
            self.entry_score_a.delete(0, tk.END)
            self.entry_score_b.delete(0, tk.END)

            if self.selected_match_id in self.sent_guesses:
                prev_a, prev_b = self.sent_guesses[self.selected_match_id]
                self.entry_score_a.insert(0, str(prev_a))
                self.entry_score_b.insert(0, str(prev_b))
                self.btn_enviar_palpite.configure(state="normal", text="Atualizar Palpite")
                self.label_aviso_palpite.configure(
                    text=f"Já submeteu um palpite para este jogo nesta sessão ({prev_a} x {prev_b}). Pode alterar!",
                    text_color="#ffb86c"
                )
            else:
                self.btn_enviar_palpite.configure(state="normal", text="Submeter Palpite")
                self.label_aviso_palpite.configure(text="")

    def desenhar_lista_partidas(self):
        """Desenha de forma legível e dinâmica os cartões de cada partida na lista."""
        # Limpar widgets anteriores do frame
        for widget in self.scroll_partidas.winfo_children():
            widget.destroy()

        if not self.all_matches:
            lbl = ctk.CTkLabel(self.scroll_partidas, text="Sem partidas disponíveis.")
            lbl.pack(pady=20)
            return

        for m in self.all_matches:
            match_id = m.get("id")
            team_a = m["team_a"].get("name", "Equipa A")
            flag_a = m["team_a"].get("flag", "")
            team_b = m["team_b"].get("name", "Equipa B")
            flag_b = m["team_b"].get("flag", "")
            status = m.get("status", "scheduled")

            card = ctk.CTkFrame(self.scroll_partidas, corner_radius=8, fg_color="#2b2b2b" if status == "finished" else "#1e1e1e")
            card.pack(fill="x", pady=6, padx=5)

            # Informação do Confronto
            if status == "finished":
                real_score = m.get("real_score", {})
                score_str = f" {real_score.get('a', 0)} - {real_score.get('b', 0)} "
                lbl_confronto = ctk.CTkLabel(
                    card, 
                    text=f"{flag_a} {team_a}  {score_str}  {team_b} {flag_b}",
                    font=ctk.CTkFont(size=14, weight="bold"),
                    text_color="#8be9fd"
                )
                lbl_confronto.pack(side="left", padx=15, pady=12)

                lbl_status = ctk.CTkLabel(card, text="Finalizado", text_color="gray", font=ctk.CTkFont(size=11))
                lbl_status.pack(side="right", padx=15)
            else:
                lbl_confronto = ctk.CTkLabel(
                    card, 
                    text=f"{flag_a} {team_a}   vs   {team_b} {flag_b}",
                    font=ctk.CTkFont(size=14)
                )
                lbl_confronto.pack(side="left", padx=15, pady=12)

                # Botão rápido para apostar nessa partida específica
                btn_apostar = ctk.CTkButton(
                    card, text="Palpitar", width=80, height=26,
                    command=lambda match_item=m: self.alternar_para_palpite_de_jogo(match_item)
                )
                btn_apostar.pack(side="right", padx=15)

    def alternar_para_palpite_de_jogo(self, match):
        """Seleciona uma partida do histórico e foca a tela na aba de Palpites."""
        self.atualizar_visual_palpite(match)
        self.tabview.set("⚽ Fazer Palpite")

    def desenhar_ranking(self, ranking_list):
        """Preenche o painel de classificação geral com uma listagem."""
        for widget in self.scroll_ranking.winfo_children():
            widget.destroy()

        if not ranking_list:
            lbl = ctk.CTkLabel(self.scroll_ranking, text="Ranking ainda não inicializado.")
            lbl.pack(pady=20)
            return

        # Cabeçalho da tabela
        header_row = ctk.CTkFrame(self.scroll_ranking, fg_color="transparent")
        header_row.pack(fill="x", pady=4, padx=5)

        ctk.CTkLabel(header_row, text="Pos.", font=ctk.CTkFont(weight="bold"), width=50, anchor="w").pack(side="left", padx=10)
        ctk.CTkLabel(header_row, text="Jogador", font=ctk.CTkFont(weight="bold"), width=250, anchor="w").pack(side="left", padx=10)
        ctk.CTkLabel(header_row, text="Pontos", font=ctk.CTkFont(weight="bold"), width=100, anchor="e").pack(side="right", padx=10)

        # Divisor de linha
        ctk.CTkFrame(self.scroll_ranking, height=2, fg_color="gray").pack(fill="x", pady=2)

        # Utilizadores rankeados
        for r in ranking_list:
            row = ctk.CTkFrame(self.scroll_ranking, fg_color="transparent")
            row.pack(fill="x", pady=3, padx=5)

            pos = r.get("ranking", "-")
            username = r.get("username", "N/A")
            points = r.get("points", 0.0)

            # Destacar Top 3
            cor_posicao = "white"
            if pos == 1:
                cor_posicao = "#ffd700"  # Ouro
                pos_str = f"🥇 {pos}º"
            elif pos == 2:
                cor_posicao = "#c0c0c0"  # Prata
                pos_str = f"🥈 {pos}º"
            elif pos == 3:
                cor_posicao = "#cd7f32"  # Bronze
                pos_str = f"🥉 {pos}º"
            else:
                pos_str = f"   {pos}º"

            ctk.CTkLabel(row, text=pos_str, font=ctk.CTkFont(weight="bold"), text_color=cor_posicao, width=50, anchor="w").pack(side="left", padx=10)
            
            # Se o utilizador logado for o da linha, destaca em verde
            is_me = (username == self.entry_username.get().strip())
            cor_nome = "#55ff55" if is_me else "white"
            lbl_user = ctk.CTkLabel(
                row, text=username if not is_me else f"{username} (Você)", 
                font=ctk.CTkFont(weight="bold" if is_me else "normal"), 
                text_color=cor_nome, width=250, anchor="w"
            )
            lbl_user.pack(side="left", padx=10)

            ctk.CTkLabel(row, text=f"{points:.1f} pts", font=ctk.CTkFont(weight="bold"), width=100, anchor="e").pack(side="right", padx=10)

    # --- ENVIO DE PALPITE COM VERIFICAÇÃO ---

    def acao_submeter_palpite(self):
        """Prepara e valida os dados de palpite antes de disparar a requisição."""
        username = self.entry_username.get().strip()
        score_a_raw = self.entry_score_a.get().strip()
        score_b_raw = self.entry_score_b.get().strip()

        # Validações Locais (Economiza requests desnecessários)
        if not username:
            self.exibir_mensagem_feedback("O username não pode estar vazio!", "red")
            return

        if not score_a_raw or not score_b_raw:
            self.exibir_mensagem_feedback("Preencha ambos os placares!", "red")
            return

        try:
            score_a = int(score_a_raw)
            score_b = int(score_b_raw)
            if score_a < 0 or score_b < 0:
                raise ValueError("Placar negativo")
        except ValueError:
            self.exibir_mensagem_feedback("Os placares devem ser números inteiros maiores ou iguais a 0!", "red")
            return

        if not self.selected_match_id:
            self.exibir_mensagem_feedback("Nenhuma partida selecionada para apostas.", "red")
            return

        # Desativa o botão temporariamente para evitar duplo clique
        self.btn_enviar_palpite.configure(state="disabled", text="A Enviar...")
        self.exibir_mensagem_feedback("A processar a aposta no servidor...", "gray")

        # Disparar envio em thread secundária para evitar travamento da UI
        threading.Thread(
            target=self.enviar_requisicao_palpite, 
            args=(self.selected_match_id, username, score_a, score_b), 
            daemon=True
        ).start()

    def enviar_requisicao_palpite(self, match_id, username, score_a, score_b):
        """Envia o POST do palpite para a API e lida com o retorno."""
        url = f"{BASE_URL}/api/match?id={match_id}"
        headers = {
            "Content-Type": "application/json",
            "X-Client-Id": CLIENT_ID
        }
        payload = {
            "username": username,
            "score_a": score_a,
            "score_b": score_b
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=5)
            
            if response.status_code == 200:
                # Sucesso
                # Atualizar histórico de palpites local para alterar botão de "Enviar" para "Atualizar"
                self.sent_guesses[match_id] = (score_a, score_b)
                
                self.exibir_mensagem_feedback("Palpite enviado/atualizado com sucesso!", "#55ff55")
                
                # Atualizar dados dinamicamente após envio
                self.label_aviso_palpite.configure(
                    text=f"Já submeteu um palpite para este jogo nesta sessão ({score_a} x {score_b}). Pode alterar!",
                    text_color="#ffb86c"
                )
                self.btn_enviar_palpite.configure(state="normal", text="Atualizar Palpite")
                
                # Força atualização do Ranking
                threading.Thread(target=self.carregar_ranking, daemon=True).start()

            elif response.status_code == 409:
                self.exibir_mensagem_feedback("Erro: Esta partida já foi finalizada!", "red")
                self.btn_enviar_palpite.configure(state="disabled", text="Apostas Encerradas")
            elif response.status_code == 400:
                err_msg = response.json().get("error", "Dados inválidos.")
                self.exibir_mensagem_feedback(f"Erro de Validação: {err_msg}", "red")
                self.btn_enviar_palpite.configure(state="normal", text="Submeter Palpite")
            else:
                self.exibir_mensagem_feedback(f"Erro inesperado do servidor (Código {response.status_code}).", "red")
                self.btn_enviar_palpite.configure(state="normal", text="Submeter Palpite")

        except Exception as e:
            self.exibir_mensagem_feedback("Erro de conexão. Verifique a internet e tente de novo.", "red")
            self.btn_enviar_palpite.configure(state="normal", text="Submeter Palpite")

    def exibir_mensagem_feedback(self, texto, cor="white"):
        """Define com segurança o texto de aviso da interface."""
        self.label_feedback.configure(text=texto, text_color=cor)


if __name__ == "__main__":
    app = BolaoApp()
    app.mainloop()
