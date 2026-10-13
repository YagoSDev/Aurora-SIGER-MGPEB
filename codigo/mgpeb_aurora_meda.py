"""MGPEB - Modulo de Gerenciamento de Pouso e Estabilizacao de Base, versao MEDA.

Atividade integradora FIAP | Missao Aurora SIGER.
Prototipo DIDATICO: os limites, condicoes e valores sao simulados; nao sao
parametros certificados para uma missao espacial real. MEDA e apenas referencia
historica: as medicoes nao correspondem a uma unica leitura simultanea.

Conteudos: listas, fila, pilha, busca linear/binaria, insertion sort,
operadores booleanos AND/OR/NOT, if/elif/else, while, for e funcao linear.
Executar: python3 mgpeb_aurora_meda.py
"""

import csv
from pathlib import Path

# ----------------------------- PARAMETROS -----------------------------
# Valores inventados apenas para permitir testes e explicar as decisoes.
COMBUSTIVEL_MINIMO = 25.0       # porcentagem simulada
VENTO_MAXIMO = 40.0             # km/h (limite didatico)
VISIBILIDADE_MINIMA = 60.0      # indice ficticio de 0 a 100 (MEDA nao mede assim)
PRESSAO_MINIMA_PA = 650.0        # faixa de estudo FICTICIA, nao e criterio NASA
PRESSAO_MAXIMA_PA = 850.0        # faixa de estudo FICTICIA, nao e criterio NASA
TEMPERATURA_SOLO_MIN_C = -90.0   # faixa de estudo FICTICIA, nao e criterio NASA
TEMPERATURA_SOLO_MAX_C = -5.0    # faixa de estudo FICTICIA, nao e criterio NASA
ARQUIVO_MEDA = Path(__file__).with_name("meda_observacoes_nasa.csv")
ALTURA_INICIAL = 4000.0         # metros
VELOCIDADE_DESCIDA = 500.0      # metros por minuto (constante)
ALTURA_APROXIMACAO = 500.0      # metros

# Cada dicionario e um modulo. Os dados abaixo sao ficticios.
MODULOS_INICIAIS = [
    {"id": "M01", "nome": "Energia", "tipo": "energia", "prioridade": 1,
     "combustivel": 67.0, "massa_kg": 6500, "criticidade": 5, "chegada_min": 15,
     "integridade": True, "sensor_principal": True, "sensor_reserva": True},
    {"id": "M02", "nome": "Habitacao", "tipo": "habitacao", "prioridade": 2,
     "combustivel": 44.0, "massa_kg": 9800, "criticidade": 5, "chegada_min": 20,
     "integridade": True, "sensor_principal": True, "sensor_reserva": False},
    {"id": "M03", "nome": "Suporte medico", "tipo": "medico", "prioridade": 3,
     "combustivel": 31.0, "massa_kg": 4600, "criticidade": 4, "chegada_min": 12,
     "integridade": True, "sensor_principal": False, "sensor_reserva": True},
    {"id": "M04", "nome": "Logistica", "tipo": "logistica", "prioridade": 4,
     "combustivel": 19.0, "massa_kg": 7900, "criticidade": 3, "chegada_min": 10,
     "integridade": True, "sensor_principal": True, "sensor_reserva": True},
    {"id": "M05", "nome": "Laboratorio cientifico", "tipo": "laboratorio",
     "prioridade": 5, "combustivel": 58.0, "massa_kg": 5500,
     "criticidade": 2, "chegada_min": 25, "integridade": False,
     "sensor_principal": True, "sensor_reserva": True},
]


def chave_de_ordenacao(modulo, criterio):
    """Devolve uma tupla para comparar os modulos no insertion sort."""
    if criterio == "prioridade":
        # Criticidade maior ganha o desempate; chegada mais cedo vem depois.
        return (modulo["prioridade"], -modulo["criticidade"],
                modulo["chegada_min"], modulo["id"])
    if criterio == "combustivel":
        return (modulo["combustivel"], modulo["chegada_min"], modulo["id"])
    if criterio == "massa":
        return (modulo["massa_kg"], modulo["chegada_min"], modulo["id"])
    if criterio == "id":
        return (modulo["id"],)
    # Ordem de chegada (criterio inicial da fila).
    return (modulo["chegada_min"], modulo["id"])


def insertion_sort(modulos, criterio="chegada"):
    """Ordenacao classica por insercao; nao usa sorted() ou sort()."""
    resultado = modulos[:]  # copia a lista, sem alterar o cadastro original
    for i in range(1, len(resultado)):
        atual = resultado[i]
        j = i - 1
        while j >= 0 and chave_de_ordenacao(resultado[j], criterio) > chave_de_ordenacao(atual, criterio):
            resultado[j + 1] = resultado[j]
            j -= 1
        resultado[j + 1] = atual
    return resultado


def busca_linear(modulos, campo, valor):
    """Percorre os modulos sem exigir ordenacao (O(n))."""
    encontrados = []
    for modulo in modulos:
        if modulo[campo] == valor:
            encontrados.append(modulo)
    return encontrados


def busca_binaria_id(modulos, identificador):
    """Busca binaria (O(log n) apos ordenar). Devolve modulo ou None."""
    ordenados = insertion_sort(modulos, "id")
    inicio, fim = 0, len(ordenados) - 1
    while inicio <= fim:
        meio = (inicio + fim) // 2
        if ordenados[meio]["id"] == identificador:
            return ordenados[meio]
        if identificador < ordenados[meio]["id"]:
            fim = meio - 1
        else:
            inicio = meio + 1
    return None


def altura(t):
    """H(t) = 4000 - 500*t durante a descida, limitada a zero metro."""
    if t < 0:
        raise ValueError("Tempo nao pode ser negativo.")
    return max(0.0, ALTURA_INICIAL - VELOCIDADE_DESCIDA * t)


def criar_sistema():
    """Cadastros em lista; fila por chegada; listas auxiliares e pilha LIFO."""
    modulos = []
    for dados in MODULOS_INICIAIS:
        modulo = dados.copy()
        modulo["status"] = "AGUARDANDO"
        modulos.append(modulo)

    por_chegada = insertion_sort(modulos, "chegada")
    return {
        "modulos": modulos,
        "fila": [m["id"] for m in por_chegada],  # FIFO, antes de priorizar
        "pousados": [],
        "espera": [],     # pouso adiado por condicao temporaria
        "alertas": [],    # falhas criticas que precisam de avaliacao
        "historico_pilha": [],  # ultimo evento e o primeiro a desfazer (LIFO)
        "condicoes": {
            "vento": 20.0,
            "visibilidade": 80.0,
            "area_livre": True,
            "alerta_global": False,
            "tempo_descida": 7.0,
            # Valores abaixo sao HIPOTETICOS ate aplicar um registro publicado.
            "pressao_pa": 720.0,
            "temperatura_solo_c": -30.0,
            # Fontes por parametro: nao presumir simultaneidade entre leituras.
            "origem": {"vento": "SIMULADO", "pressao_pa": "SIMULADO",
                       "temperatura_solo_c": "SIMULADO"},
        },
    }


def reorganizar_fila(sistema, criterio):
    """Reorganiza a fila por um criterio operacional (fila com prioridade)."""
    if criterio not in ("chegada", "prioridade", "combustivel", "massa"):
        raise ValueError("Criterio de ordenacao invalido.")
    modulos_fila = [busca_binaria_id(sistema["modulos"], mid) for mid in sistema["fila"]]
    ordenados = insertion_sort(modulos_fila, criterio)
    sistema["fila"] = [m["id"] for m in ordenados]


def avaliar_pouso(modulo, condicoes):
    """Representacao de AND, OR e NOT com resultados auditaveis.

    P = C AND V AND PS AND TS AND I AND (S1 OR S2) AND A AND NOT G AND H
      C: combustivel; V: vento/visibilidade; PS: pressao do ambiente;
      TS: temperatura do solo (proxy academico, nao criterio de pouso NASA);
      I: integridade;
      S1, S2: sensores redundantes; A: area livre;
      G: alerta global; H: altitude compativel com aproximacao final.
    """
    combustivel_ok = modulo["combustivel"] >= COMBUSTIVEL_MINIMO
    atmosfera_ok = (condicoes["vento"] <= VENTO_MAXIMO and
                    condicoes["visibilidade"] >= VISIBILIDADE_MINIMA)
    # Limites didaticos aplicados a um hipotetico modulo: nao autorizam pousos reais.
    pressao_ok = PRESSAO_MINIMA_PA <= condicoes["pressao_pa"] <= PRESSAO_MAXIMA_PA
    temperatura_ok = (TEMPERATURA_SOLO_MIN_C <= condicoes["temperatura_solo_c"]
                      <= TEMPERATURA_SOLO_MAX_C)
    integridade_ok = modulo["integridade"]
    sensores_ok = modulo["sensor_principal"] or modulo["sensor_reserva"]
    area_ok = condicoes["area_livre"]
    sem_alerta = not condicoes["alerta_global"]
    altitude_ok = altura(condicoes["tempo_descida"]) <= ALTURA_APROXIMACAO

    autorizado = (combustivel_ok and atmosfera_ok and pressao_ok and temperatura_ok and integridade_ok
                  and sensores_ok and area_ok and sem_alerta and altitude_ok)
    motivos = []
    verificacoes = [
        (combustivel_ok, "Combustivel abaixo do minimo simulado"),
        (atmosfera_ok, "Condicoes atmosfericas inadequadas (vento/visibilidade)"),
        (pressao_ok, "Pressao fora do intervalo didatico"),
        (temperatura_ok, "Temperatura do solo fora do intervalo didatico"),
        (integridade_ok, "Integridade estrutural comprometida"),
        (sensores_ok, "Ambos os sensores indisponiveis"),
        (area_ok, "Area de pouso ocupada"),
        (sem_alerta, "Alerta global de seguranca ativo"),
        (altitude_ok, "Modulo ainda acima da altitude de aproximacao"),
    ]
    for resultado, motivo in verificacoes:
        if not resultado:
            motivos.append(motivo)
    return autorizado, motivos


def processar_proximo(sistema):
    """Remove o primeiro da fila; registra pouso ou envia para lista de alertas."""
    if not sistema["fila"]:
        return None, "Fila vazia.", []

    identificador = sistema["fila"][0]
    modulo = busca_binaria_id(sistema["modulos"], identificador)
    autorizado, motivos = avaliar_pouso(modulo, sistema["condicoes"])

    # Registro para DESFAZER antes de qualquer alteracao no estado.
    # Falhas de hardware/combustivel exigem alerta; demais causam espera.
    falhas_criticas = (
        "Combustivel abaixo do minimo simulado",
        "Integridade estrutural comprometida",
        "Ambos os sensores indisponiveis",
    )
    alerta_critico = any(motivo in falhas_criticas for motivo in motivos)
    destino = "pousados" if autorizado else ("alertas" if alerta_critico else "espera")
    sistema["historico_pilha"].append({
        "id": identificador,
        "area_livre_antes": sistema["condicoes"]["area_livre"],
        "status_antes": modulo["status"],
        "destino": destino,
    })

    sistema["fila"].pop(0)  # atendimento da frente da fila
    if autorizado:
        modulo["status"] = "POUSADO"
        sistema["pousados"].append(identificador)
        sistema["condicoes"]["area_livre"] = False
        return modulo, "POUSO AUTORIZADO", []

    if alerta_critico:
        modulo["status"] = "ALERTA"
        sistema["alertas"].append(identificador)
        return modulo, "POUSO BLOQUEADO - ALERTA", motivos

    modulo["status"] = "EM ESPERA"
    sistema["espera"].append(identificador)
    return modulo, "POUSO ADIADO - EM ESPERA", motivos


def desfazer_ultimo(sistema):
    """Usa pilha LIFO para desfazer a ultima decisao de pouso/alerta."""
    if not sistema["historico_pilha"]:
        return None
    evento = sistema["historico_pilha"].pop()
    identificador = evento["id"]
    sistema[evento["destino"]].remove(identificador)
    sistema["fila"].insert(0, identificador)
    modulo = busca_binaria_id(sistema["modulos"], identificador)
    modulo["status"] = evento["status_antes"]
    sistema["condicoes"]["area_livre"] = evento["area_livre_antes"]
    return identificador


def recolocar_em_espera(sistema, identificador):
    """Recoloca no final da fila um modulo cujo adiamento foi temporario."""
    if identificador not in sistema["espera"]:
        return False
    sistema["espera"].remove(identificador)
    modulo = busca_binaria_id(sistema["modulos"], identificador)
    modulo["status"] = "AGUARDANDO"
    sistema["fila"].append(identificador)
    # A decisao anterior foi superada: nao pode ser desfeita isoladamente.
    sistema["historico_pilha"] = [evento for evento in sistema["historico_pilha"]
                                 if evento["id"] != identificador]
    return True


def cadastrar_modulo(sistema, dados):
    """Inclui modulo na lista e no fim da fila (quando nao existe o mesmo ID)."""
    if busca_binaria_id(sistema["modulos"], dados["id"]) is not None:
        raise ValueError("Ja existe um modulo com esse identificador.")
    novo = dados.copy()
    novo["status"] = "AGUARDANDO"
    sistema["modulos"].append(novo)
    sistema["fila"].append(novo["id"])


def mostrar_modulo(modulo):
    print(f"{modulo['id']} | {modulo['nome']} | status: {modulo['status']}")
    print(f"  tipo={modulo['tipo']} | prioridade={modulo['prioridade']} | "
          f"criticidade={modulo['criticidade']} | combustivel={modulo['combustivel']:.1f}%")
    print(f"  massa={modulo['massa_kg']:.0f} kg | chegada={modulo['chegada_min']} min | "
          f"integridade={modulo['integridade']} | "
          f"sensores={modulo['sensor_principal']}/{modulo['sensor_reserva']}")


def pedir_numero(mensagem, minimo=None, maximo=None, inteiro=False):
    """Validacao simples de entrada para uso pelo operador."""
    while True:
        try:
            texto = input(mensagem).strip().replace(",", ".")
            valor = int(texto) if inteiro else float(texto)
            if (minimo is not None and valor < minimo) or (maximo is not None and valor > maximo):
                print(f"Use um valor entre {minimo} e {maximo}.")
                continue
            return valor
        except ValueError:
            print("Numero invalido; tente novamente.")


def pedir_booleano(mensagem):
    while True:
        resposta = input(mensagem + " (s/n): ").strip().lower()
        if resposta in ("s", "sim"):
            return True
        if resposta in ("n", "nao", "não"):
            return False
        print("Digite s ou n.")


def menu_busca(sistema):
    print("1: ID (binaria) | 2: tipo (linear) | 3: prioridade (linear) | "
          "4: modulos com combustivel abaixo do minimo (linear)")
    escolha = input("Busca: ").strip()
    if escolha == "1":
        identificador = input("ID (ex.: M02): ").strip().upper()
        modulo = busca_binaria_id(sistema["modulos"], identificador)
        encontrados = [modulo] if modulo else []
    elif escolha == "2":
        tipo = input("Tipo (ex.: energia): ").strip().lower()
        encontrados = busca_linear(sistema["modulos"], "tipo", tipo)
    elif escolha == "3":
        prioridade = pedir_numero("Prioridade: ", 1, 99, inteiro=True)
        encontrados = busca_linear(sistema["modulos"], "prioridade", prioridade)
    elif escolha == "4":
        encontrados = []
        for modulo in sistema["modulos"]:
            if modulo["combustivel"] < COMBUSTIVEL_MINIMO:
                encontrados.append(modulo)
    else:
        print("Opcao invalida.")
        return
    if encontrados:
        for modulo in encontrados:
            mostrar_modulo(modulo)
    else:
        print("Nenhum modulo encontrado.")


def menu_cadastro(sistema):
    print("Cadastro de modulo ficticio")
    dados = {"id": input("ID: ").strip().upper(),
             "nome": input("Nome: ").strip(),
             "tipo": input("Tipo: ").strip().lower()}
    if not dados["id"] or not dados["nome"] or not dados["tipo"]:
        print("ID, nome e tipo sao obrigatorios.")
        return
    dados["prioridade"] = pedir_numero("Prioridade (1=maior): ", 1, 99, inteiro=True)
    dados["criticidade"] = pedir_numero("Criticidade (1..5): ", 1, 5, inteiro=True)
    dados["combustivel"] = pedir_numero("Combustivel (%): ", 0, 100)
    dados["massa_kg"] = pedir_numero("Massa (kg): ", 1)
    dados["chegada_min"] = pedir_numero("Chegada estimada a orbita (min): ", 0)
    dados["integridade"] = pedir_booleano("Estrutura integra?")
    dados["sensor_principal"] = pedir_booleano("Sensor principal disponivel?")
    dados["sensor_reserva"] = pedir_booleano("Sensor reserva disponivel?")
    try:
        cadastrar_modulo(sistema, dados)
        print("Modulo cadastrado no fim da fila.")
    except ValueError as erro:
        print(erro)


def tabela_altitude():
    print("Modelo linear: H(t) = max(0, 4000 - 500*t)")
    print("t: minutos | H(t): metros | barras (cada # = 250 m)")
    for minuto in range(0, 10):
        h = altura(minuto)
        print(f"{minuto:>3}         | {h:>5.0f}        | {'#' * int(h / 250)}")
    print("A altitude decresce 500 m/min ate 0; "
          "a aproximacao final inicia em H <= 500 m (t >= 7 min).")
    print("Modelo ficticio de velocidade constante, sem aerodinamica real.")


def apresentar_resumo(sistema):
    print("\n=== RELATORIO DA OPERACAO ===")
    for nome in ("fila", "pousados", "espera", "alertas"):
        print(f"{nome.upper()}: {', '.join(sistema[nome]) or 'nenhum'}")
    c = sistema["condicoes"]
    print(f"Pressao={c['pressao_pa']} Pa | Temperatura do solo={c['temperatura_solo_c']} C")
    print("Fontes:", c["origem"])
    print(f"Vento={c['vento']} km/h | Visibilidade didatica={c['visibilidade']} "
          f"| Area livre={c['area_livre']} | Alerta global={c['alerta_global']}")
    print(f"Altura simulada={altura(c['tempo_descida']):.1f} m")
    print("Operacoes reversiveis na pilha:", len(sistema["historico_pilha"]))


def carregar_referencias_meda():
    """Le CSV de observacoes publicadas no boletim inicial da NASA/JPL.

    Um registro de temperatura NAO implica simultaneidade com pressao ou vento.
    """
    with ARQUIVO_MEDA.open(encoding="utf-8", newline="") as arquivo:
        return list(csv.DictReader(arquivo, delimiter=";"))


def mostrar_referencias_meda():
    """Mostra proveniencia, periodo e medida antes de usar valores historicos."""
    print("\n=== REFERENCIAS HISTORICAS MEDA / NASA-JPL ===")
    print("Nao sao dados em tempo real. Valores de periodos diferentes.")
    try:
        for registro in carregar_referencias_meda():
            sufixo = " (~)" if registro["aproximado"] == "sim" else ""
            print(f"{registro['id']} | {registro['periodo']} | "
                  f"{registro['variavel']} = {registro['valor']} {registro['unidade']}{sufixo}")
            print("  ", registro["contexto"])
    except FileNotFoundError:
        print("CSV de referencias MEDA nao encontrado ao lado do script.")


def aplicar_observacao_meda(sistema, identificador):
    """Aplica UMA medicao real publicada ao cenario ACADEMICO.

    Temperatura publicada se refere a medicao proxima da superficie em Jezero,
    NAO a medicao da atmosfera ao longo da trajetoria da nave.
    """
    observacoes = carregar_referencias_meda()
    escolhido = next((r for r in observacoes if r["id"] == identificador), None)
    if escolhido is None:
        raise KeyError("Registro MEDA nao encontrado")
    valor = float(escolhido["valor"])
    c = sistema["condicoes"]
    variavel = escolhido["variavel"]
    if variavel == "rajada_vento_ms":
        parametro = "vento"
        valor *= 3.6  # m/s -> km/h; rajada, nao vento medio
    elif variavel in ("temperatura_solo_c", "pressao_pa"):
        parametro = variavel
    else:
        raise ValueError("Variavel sem suporte no prototipo")
    c[parametro] = valor
    c["origem"][parametro] = (f"NASA/JPL {escolhido['id']}: "
                               f"{escolhido['periodo']}")
    return parametro, valor


def temperatura_superficie_meda(minutos):
    """Interpolacao LINEAR DIDATICA, nao modelo fisico geral de Marte.

    Primeiro relato MEDA: ~-20 C no inicio, -25.6 C apos 30 minutos.
    T(t) = -20 + [(-25.6)-(-20)]*t/30, apenas para 0 <= t <= 30 min.
    """
    if minutos < 0 or minutos > 30:
        raise ValueError("Modelo historico limitado aos primeiros 30 minutos")
    return -20.0 + ((-25.6 + 20.0) / 30.0) * minutos


def tabela_temperatura_meda():
    print("\n=== MODELO MATEMATICO INSPIRADO NO MEDA ===")
    print("T(t) = -20 - (5.6/30)*t; t em minutos, T em graus Celsius")
    print("Interpolacao entre duas observacoes, primeiro registro de 19/02/2021.")
    print("O valor inicial e aproximado, nao e previsao meteorologica universal.")
    for minuto in (0, 5, 10, 15, 20, 25, 30):
        print(f"t={minuto:>2} min | T={temperatura_superficie_meda(minuto):>6.2f} C")


def menu():
    sistema = criar_sistema()
    print("\nMISSÃO AURORA SIGER - MGPEB | SIMULACAO DIDATICA")
    while True:
        print("\n1 Listar modulos    2 Ver fila             3 Buscar")
        print("4 Ordenar fila      5 Avaliar proximo       6 Alterar ambiente")
        print("7 Liberar area      8 Desfazer ultima acao  9 Modelo de altitude")
        print("10 Resumo           11 Cadastrar modulo     12 Recolocar espera")
        print("13 Ver MEDA NASA     14 Aplicar observacao   15 Modelo de temperatura")
        print("0 Sair")
        opcao = input("Escolha: ").strip()
        if opcao == "0":
            print("Encerrando a simulacao.")
            break
        elif opcao == "1":
            for modulo in sistema["modulos"]:
                mostrar_modulo(modulo)
        elif opcao == "2":
            print("FILA (frente -> fim):", " -> ".join(sistema["fila"]) or "vazia")
        elif opcao == "3":
            menu_busca(sistema)
        elif opcao == "4":
            print("1 Prioridade | 2 Menor combustivel | 3 Chegada | 4 Menor massa")
            criterio = {"1": "prioridade", "2": "combustivel", "3": "chegada", "4": "massa"}.get(input("Criterio: ").strip())
            if criterio is None:
                print("Opcao invalida.")
            else:
                reorganizar_fila(sistema, criterio)
                print("Fila reorganizada:", " -> ".join(sistema["fila"]))
        elif opcao == "5":
            modulo, resultado, motivos = processar_proximo(sistema)
            print(resultado)
            if modulo:
                print("Modulo:", modulo["id"], "-", modulo["nome"])
                for motivo in motivos:
                    print(" -", motivo)
        elif opcao == "6":
            c = sistema["condicoes"]
            c["vento"] = pedir_numero("Vento/rajada simulada (km/h): ", 0)
            c["pressao_pa"] = pedir_numero("Pressao simulada (Pa): ", 0)
            c["temperatura_solo_c"] = pedir_numero("Temperatura do solo simulada (C): ", -150, 80)
            for parametro in ("vento", "pressao_pa", "temperatura_solo_c"):
                c["origem"][parametro] = "SIMULADO"
            c["visibilidade"] = pedir_numero("Indice de visibilidade (0..100): ", 0, 100)
            c["tempo_descida"] = pedir_numero("Tempo de descida (min): ", 0)
            c["alerta_global"] = pedir_booleano("Alerta global ativo?")
            print("Ambiente atualizado com entradas manuais (simuladas).")
        elif opcao == "7":
            sistema["condicoes"]["area_livre"] = True
            print("Area liberada para o proximo pouso.")
        elif opcao == "8":
            identificado = desfazer_ultimo(sistema)
            print("Ultima decisao desfeita para", identificado) if identificado else print("Pilha vazia.")
        elif opcao == "9":
            tabela_altitude()
        elif opcao == "10":
            apresentar_resumo(sistema)
        elif opcao == "11":
            menu_cadastro(sistema)
        elif opcao == "12":
            print("Em espera:", ", ".join(sistema["espera"]) or "nenhum")
            identificador = input("ID para recolocar no fim da fila: ").strip().upper()
            if recolocar_em_espera(sistema, identificador):
                print("Modulo retornou a fila para nova tentativa.")
            else:
                print("O modulo nao esta em espera.")
        elif opcao == "13":
            mostrar_referencias_meda()
        elif opcao == "14":
            mostrar_referencias_meda()
            identificador = input("ID da observacao (MEDA01..MEDA04): ").strip().upper()
            try:
                parametro, valor = aplicar_observacao_meda(sistema, identificador)
                print(f"Aplicado {parametro} = {valor:.2f} ao ambiente SIMULADO.")
                print("ATENCAO: leituras historicas distintas, nao sao telemetria de pouso.")
            except (KeyError, ValueError, FileNotFoundError) as erro:
                print("Falha:", erro)
        elif opcao == "15":
            tabela_temperatura_meda()
        else:
            print("Opcao invalida.")


if __name__ == "__main__":
    try:
        menu()
    except (EOFError, KeyboardInterrupt):
        print("\nSimulacao encerrada pelo operador.")
