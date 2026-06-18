import random
import sys
import pygame

pygame.init()
pygame.font.init()

LARGURA, ALTURA = 800, 600
tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("RPG Primeira Pessoa - Com Banco de Textos")
relogio = pygame.time.Clock()

COR_BG = (10, 10, 12)
COR_TEXTO = (255, 255, 255)
COR_CAIXA_PRETA = (0, 0, 0)
COR_BOTAO = (70, 130, 180)
COR_BOTAO_HOVER = (100, 149, 237)
COR_BOTAO_ALVO = (147, 112, 219) 
COR_BOTAO_RESET = (178, 34, 34)

NEON_COMBATENTE = (50, 205, 50)   
NEON_ARQUEIRO = (255, 140, 0)    
NEON_MAGO = (138, 43, 226)      

fonte_principal = pygame.font.SysFont("Arial", 16)
fonte_titulo = pygame.font.SysFont("Arial", 24, bold=True)
fonte_vida = pygame.font.SysFont("Arial", 14, bold=True)


class Entidade:
    def __init__(self, nome, classe, hp_max, resistencia, esquiva, cor_neon):
        self.nome = nome
        self.classe = classe
        self.hp_max = hp_max
        self.hp = hp_max
        self.resistencia = resistencia  
        self.esquiva = esquiva          
        self.cor_neon = cor_neon
        self.bloqueando = False
        self.x = 0
        self.y = 0
        self.modificadores = {"critico": 1.0, "defesa_extra": 0}

    def esta_vivo(self):
        return self.hp > 0


class Jogador(Entidade):
    def __init__(self, nome, classe, hp_max, resistencia, esquiva, cor_neon):
        super().__init__(nome, classe, hp_max, resistencia, esquiva, cor_neon)
        self.potacoes_restantes = 3

    def tomar_dano(self, dano_bruto):
        defesa_total = self.resistencia + self.modificadores["defesa_extra"]
        if self.bloqueando:
            defesa_total *= 2

        dano_final = max(1, int(dano_bruto - defesa_total))
        self.hp = max(0, self.hp - dano_final)
        return dano_final


class Inimigo(Entidade):
    def __init__(self, nome, classe, hp_max, resistencia, esquiva, cor_neon, pos_x):
        super().__init__(nome, classe, hp_max, resistencia, esquiva, cor_neon)
        self.x = pos_x
        self.y = 180  
        self.dano_ataque = 12
        self.configurar_classe()

    def configurar_classe(self):
        if self.classe == "Mago":
            self.dano_ataque = 22      
        elif self.classe == "Arqueiro":
            self.dano_ataque = 14
        else:
            self.dano_ataque = 10

    def calcular_dano_recebido(self, valor_ataque, d20):
        if self.classe == "Arqueiro" and random.randint(1, 100) <= self.esquiva and d20 != 20:
            return False, 0
        
        dano_final = max(1, valor_ataque - self.resistencia)
        self.hp = max(0, self.hp - dano_final)
        return True, dano_final

    def desenhar_corpo(self, superficie):
        cx, cy = self.x, self.y
        if self.classe == "Combatente":
            pygame.draw.rect(superficie, self.cor_neon, (cx - 30, cy - 30, 60, 60), 3)
            pygame.draw.rect(superficie, COR_TEXTO, (cx - 20, cy - 10, 8, 35)) 
        elif self.classe == "Arqueiro":
            pygame.draw.polygon(superficie, self.cor_neon, [(cx, cy - 40), (cx - 25, cy + 20), (cx + 25, cy + 20)], 3)
            pygame.draw.line(superficie, COR_TEXTO, (cx - 15, cy), (cx + 15, cy), 2) 
        elif self.classe == "Mago":
            pygame.draw.circle(superficie, self.cor_neon, (cx, cy + 5), 22, 3)
            pygame.draw.polygon(superficie, self.cor_neon, [(cx - 20, cy - 12), (cx, cy - 45), (cx + 20, cy - 12)], 2)


class Jogo:
    def __init__(self):
        self.recorde_ondas = 0  
        self.log_mensagens = [] 
        self.timer_animacao = 0
        self.tipo_animacao = None
        self.alvo_animacao_x = 0
        self.resetar_jogo()

    def adicionar_log(self, texto):
        self.log_mensagens.append(texto)
        if len(self.log_mensagens) > 4:
            self.log_mensagens.pop(0)

    def resetar_jogo(self):
        self.jogador = Jogador("Você (Guerreiro)", "Guerreiro", hp_max=200, resistencia=8, esquiva=5, cor_neon=COR_TEXTO)
        self.onda_atual = 1
        self.ondas_vencidas = 0
        self.inimigos = []
        self.log_mensagens = []
        self.adicionar_log("--- Nova Jornada Iniciada ---")
        self.adicionar_log("Inimigos à vista na sua frente! Prepare sua espada.")
        self.gerar_onda()
        self.escolhendo_alvo = False 

    def rolar_d20(self):
        return random.randint(1, 20)

    def gerar_onda(self):
        self.inimigos = []
        qtd_inimigos = random.randint(1, 3)
        
        if qtd_inimigos == 1:
            posicoes_x = [400]
        elif qtd_inimigos == 2:
            posicoes_x = [280, 520]
        else:
            posicoes_x = [200, 400, 600]

        pool_classes = [
            {"classe": "Combatente", "hp": 90, "res": 14, "esq": 5, "cor": NEON_COMBATENTE},
            {"classe": "Arqueiro", "hp": 65, "res": 4, "esq": 40, "cor": NEON_ARQUEIRO},
            {"classe": "Mago", "hp": 35, "res": 0, "esq": 10, "cor": NEON_MAGO}
        ]
         
        for i in range(qtd_inimigos):
            dados_classe = random.choice(pool_classes)
            px = posicoes_x[i]
            
            ini = Inimigo(
                nome=f"{dados_classe['classe']} {i+1}",
                classe=dados_classe['classe'],
                hp_max=dados_classe['hp'],
                resistencia=dados_classe['res'],
                esquiva=dados_classe['esq'],
                cor_neon=dados_classe['cor'],
                pos_x=px
            )
            self.inimigos.append(ini)

    def processar_turno_inimigos(self):
        if not self.jogador.esta_vivo():
            return

        for ini in self.inimigos:
            if ini.esta_vivo():
                dano_causado = self.jogador.tomar_dano(ini.dano_ataque)
                self.adicionar_log(f"⚔️ {ini.nome} contra-atacou e causou {dano_causado} de dano!")
        
        self.adicionar_log("Sua vez! Escolha uma ação de combate.")
        self.jogador.bloqueando = False 

    def realizar_ataque(self, indice_alvo):
        alvo = self.inimigos[indice_alvo]
        d20 = self.rolar_d20()
        
        self.tipo_animacao = "ESPADA"
        self.alvo_animacao_x = alvo.x
        self.timer_animacao = 18
        
        if d20 == 1:
            self.adicionar_log(f" D20: 1 (Falha Crítica)! Você errou feio o corte no {alvo.nome}!")
        else:
            dano = random.randint(25, 35)
            if d20 == 20: 
                dano = int(dano * 2 * self.jogador.modificadores["critico"])
                _, dano_causado = alvo.calcular_dano_recebido(dano, d20)
                self.adicionar_log(f" D20: 20! CORTE CRÍTICO! {alvo.nome} sofreu {dano_causado} de dano!")
            else: 
                dano += d20
                sucesso, dano_causado = alvo.calcular_dano_recebido(dano, d20)
                if sucesso:
                    self.adicionar_log(f" D20: {d20}. Você golpeou {alvo.nome} causando {dano_causado} de dano.")
                else:
                    self.adicionar_log(f" {alvo.nome} saltou para o lado e esquivou do seu ataque!")

        self.escolhendo_alvo = False

    def acionar_bloqueio(self):
        self.jogador.bloqueando = True
        self.tipo_animacao = "ESCUDO"
        self.timer_animacao = 18
        self.adicionar_log(" Você ergueu o escudo! Próximos danos recebidos serão reduzidos.")

    def usar_pocao(self):
        if self.jogador.potacoes_restantes > 0:
            self.jogador.hp = min(self.jogador.hp_max, self.jogador.hp + 75)
            self.jogador.potacoes_restantes -= 1
            self.tipo_animacao = "POCAO"
            self.timer_animacao = 18
            self.adicionar_log(" Você bebeu uma poção e recuperou 75 pontos de vida!")
        else:
            self.adicionar_log(" Você tateia o cinto, mas suas poções acabaram!")


def finalizar_rodada(jogo):
    if not any(i.esta_vivo() for i in jogo.inimigos):
        jogo.ondas_vencidas += 1
        if jogo.ondas_vencidas > jogo.recorde_ondas:
            jogo.recorde_ondas = jogo.ondas_vencidas
        jogo.onda_atual += 1
        jogo.adicionar_log(f"🌟 Vitória! Sala limpa. Avançando para a Onda {jogo.onda_atual}!")
        jogo.gerar_onda()
    else:
        jogo.processar_turno_inimigos()


def desenhar_interface(jogo):
    tela.fill(COR_BG)

    pygame.draw.rect(tela, COR_CAIXA_PRETA, (50, 370, 700, 100))
    pygame.draw.rect(tela, (50, 50, 60), (50, 370, 700, 100), 2)
    
    for idx, msg in enumerate(jogo.log_mensagens):
        cor_linha = (160, 160, 160) if idx < len(jogo.log_mensagens) - 1 else COR_TEXTO
        txt_renderizado = fonte_principal.render(msg, True, cor_linha)
        tela.blit(txt_renderizado, (65, 375 + (idx * 22)))

    for ini in jogo.inimigos:
        if ini.esta_vivo():
            ini.desenhar_corpo(tela)
            
            pygame.draw.rect(tela, (100, 0, 0), (ini.x - 50, ini.y + 45, 100, 7))
            largura_barra = int((ini.hp / ini.hp_max) * 100)
            pygame.draw.rect(tela, ini.cor_neon, (ini.x - 50, ini.y + 45, largura_barra, 7))
            
            txt_nome_ini = fonte_vida.render(f"{ini.nome} [{ini.hp}/{ini.hp_max}]", True, COR_TEXTO)
            tela.blit(txt_nome_ini, txt_nome_ini.get_rect(center=(ini.x, ini.y + 65)))

    if jogo.timer_animacao > 0:
        jogo.timer_animacao -= 1
        if jogo.tipo_animacao == "ESPADA":
            ex = jogo.alvo_animacao_x
            pygame.draw.line(tela, (255, 255, 255), (ex - 35, 140), (ex + 35, 210), 6)
            pygame.draw.line(tela, (0, 191, 255), (ex - 30, 135), (ex + 30, 205), 2)
        elif jogo.tipo_animacao == "ESCUDO":
            pygame.draw.polygon(tela, (30, 144, 255), [(365, 230), (435, 230), (425, 285), (400, 305), (375, 285)])
            pygame.draw.polygon(tela, COR_TEXTO, [(365, 230), (435, 230), (425, 285), (400, 305), (375, 285)], 2)
        elif jogo.tipo_animacao == "POCAO":
            pygame.draw.rect(tela, (220, 20, 60), (385, 240, 30, 42))
            pygame.draw.rect(tela, (124, 252, 0), (394, 225, 12, 15))
            pygame.draw.rect(tela, COR_TEXTO, (385, 240, 30, 42), 2)

        if jogo.timer_animacao == 0:
            finalizar_rodada(jogo)

    pygame.draw.rect(tela, COR_CAIXA_PRETA, (50, 520, 700, 70))
    pygame.draw.rect(tela, (192, 192, 192), (50, 520, 700, 70), 2)

    mouse_pos = pygame.mouse.get_pos()
    clicou = pygame.mouse.get_pressed()[0]
    acao_selecionada = None

    if jogo.jogador.esta_vivo():
        txt_seu_hp_num = fonte_vida.render(f"GUERREIRO (Você)   HP: {jogo.jogador.hp} / {jogo.jogador.hp_max}", True, COR_TEXTO)
        tela.blit(txt_seu_hp_num, (60, 525))
        
        pygame.draw.rect(tela, (150, 0, 0), (350, 527, 200, 10))
        largura_sua_vida = int((jogo.jogador.hp / jogo.jogador.hp_max) * 200)
        pygame.draw.rect(tela, (0, 220, 50), (350, 527, largura_sua_vida, 10))

        txt_pot = fonte_vida.render(f"Poções: {jogo.jogador.potacoes_restantes}", True, (218, 165, 32))
        tela.blit(txt_pot, (575, 525))
        txt_vits = fonte_vida.render(f"Ondas Vencidas: {jogo.ondas_vencidas}", True, COR_TEXTO)
        tela.blit(txt_vits, (655, 525))

        if jogo.timer_animacao == 0:
            if not jogo.escolhendo_alvo:
                botoes = [
                    ("ATACAR", (60, 548, 140, 35), "MENU_ALVO"), 
                    ("BLOQUEAR", (210, 548, 140, 35), "ACT_BLOQUEAR"), 
                    ("POÇÃO", (360, 548, 140, 35), "POTION")
                ]
                for nome, ret, acao in botoes:
                    rect_obj = pygame.Rect(ret)
                    if rect_obj.collidepoint(mouse_pos):
                        pygame.draw.rect(tela, COR_BOTAO_HOVER, rect_obj)
                        if clicou: acao_selecionada = acao
                    else:
                        pygame.draw.rect(tela, COR_BOTAO, rect_obj)
                    pygame.draw.rect(tela, COR_TEXTO, rect_obj, 1)
                    texto_btn = fonte_vida.render(nome, True, COR_TEXTO)
                    tela.blit(texto_btn, texto_btn.get_rect(center=rect_obj.center))
            else:
                pos_btn_x = 60
                for i, ini in enumerate(jogo.inimigos):
                    if ini.esta_vivo():
                        rect_alvo = pygame.Rect((pos_btn_x, 548, 120, 35))
                        if rect_alvo.collidepoint(mouse_pos):
                            pygame.draw.rect(tela, COR_TEXTO, rect_alvo)
                            texto_cor = (0, 0, 0)
                            if clicou: acao_selecionada = f"ALVO_{i}"
                        else:
                            pygame.draw.rect(tela, COR_BOTAO_ALVO, rect_alvo)
                            texto_cor = COR_TEXTO
                            
                        pygame.draw.rect(tela, COR_TEXTO, rect_alvo, 1)
                        txt_btn_alvo = fonte_vida.render(ini.nome, True, texto_cor)
                        tela.blit(txt_btn_alvo, txt_btn_alvo.get_rect(center=rect_alvo.center))
                        pos_btn_x += 130
                
                rect_voltar = pygame.Rect((520, 548, 80, 35))
                if rect_voltar.collidepoint(mouse_pos):
                    pygame.draw.rect(tela, (200, 20, 20), rect_voltar)
                    if clicou: acao_selecionada = "VOLTAR"
                else:
                    pygame.draw.rect(tela, COR_BOTAO_RESET, rect_voltar)
                pygame.draw.rect(tela, COR_TEXTO, rect_voltar, 1)
                txt_voltar = fonte_vida.render("Voltar", True, COR_TEXTO)
                tela.blit(txt_voltar, txt_voltar.get_rect(center=rect_voltar.center))
    else:
        rect_reset = pygame.Rect((310, 538, 180, 35))
        if rect_reset.collidepoint(mouse_pos):
            pygame.draw.rect(tela, (220, 20, 60), rect_reset)
            if clicou: acao_selecionada = "RESET"
        else:
            pygame.draw.rect(tela, COR_BOTAO_RESET, rect_reset)
        pygame.draw.rect(tela, COR_TEXTO, rect_reset, 1)
        txt_reset = fonte_vida.render("Renascer", True, COR_TEXTO)
        tela.blit(txt_reset, txt_reset.get_rect(center=rect_reset.center))

    pygame.display.flip()
    return acao_selecionada


def main():
    jogo = Jogo()
    executando = True
    travar_clique = False

    while executando:
        relogio.tick(30)
        
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                executando = False

        acao = desenhar_interface(jogo)

        if acao and not travar_clique:
            if acao == "RESET":
                jogo.resetar_jogo()
            elif acao == "MENU_ALVO":
                jogo.escolhendo_alvo = True
            elif acao == "VOLTAR":
                jogo.escolhendo_alvo = False
            elif acao == "ACT_BLOQUEAR":
                jogo.acionar_bloqueio()
            elif acao == "POTION":
                jogo.usar_pocao()
            elif acao.startswith("ALVO_"):
                indice = int(acao.split("_")[1])
                jogo.realizar_ataque(indice)
                
            travar_clique = True 

        if not pygame.mouse.get_pressed()[0]:
            travar_clique = False

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()