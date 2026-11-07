"""Course and lesson content from the original backend-video showcase."""

TEACHERS = {
    "professor": "Prof. Fulano da Silva",
    "clara": "Dra. Clara Mendonça",
    "rafael": "Prof. Rafael Costa",
    "marina": "Profa. Marina Lopes",
    "lucas": "Prof. Lucas Ribeiro",
    "andre": "Prof. André Nascimento",
}

# key, title, teacher, cover, subject, area, exams, summary, price, published, audience
COURSES = (
    ("fisica-quantica", "Introdução à Física Quântica", "professor", "fisica-quantica.webp", "Física", "Ciências da Natureza", ["ENEM", "FUVEST"],
     "Conceitos fundamentais da física moderna para vestibulares.", "29.90", True, "Estudantes que querem revisar física moderna para o ENEM e vestibulares."),
    ("fisica-enem-mecanica", "Física para o ENEM: Mecânica", "professor", "fisica-mecanica.webp", "Física", "Ciências da Natureza", ["ENEM"],
     "Aprenda cinemática, dinâmica e energia com foco nas situações mais frequentes do ENEM.", "0.00", True, "Estudantes que querem revisar os principais temas de mecânica para o ENEM."),
    ("termodinamica", "Termodinâmica Avançada", "professor", "teacher-thermo.png", "Física", "Ciências da Natureza", ["FUVEST"],
     "Curso em preparação sobre processos e ciclos termodinâmicos.", "24.90", False, "Estudantes que querem aprofundar seus conhecimentos de termodinâmica."),
    ("biologia-celular", "Biologia Celular para Vestibulares", "clara", "biologia-celular.webp", "Biologia", "Ciências da Natureza", ["ENEM", "UNICAMP"],
     "Explore organelas, metabolismo e divisão celular com foco nas questões mais cobradas.", "24.90", True, "Estudantes que desejam dominar citologia e os temas mais recorrentes nas provas."),
    ("estatistica-essencial", "Estatística Essencial", "rafael", "estatistica.webp", "Matemática", "Matemática", ["ENEM", "FUVEST"],
     "Interprete gráficos, tabelas e medidas estatísticas com segurança para a prova.", "0.00", True, "Estudantes que precisam interpretar dados e resolver questões de estatística básica."),
    ("redacao-nota-mil", "Redação nota mil: da tese à conclusão", "marina", "redacao-nota-mil.webp", "Redação", "Linguagens", ["ENEM"],
     "Construa argumentos consistentes e pratique cada etapa do texto dissertativo.", "34.90", True, "Estudantes que querem planejar e escrever redações dissertativas com mais segurança."),
    ("quimica-organica", "Química Orgânica sem mistério", "lucas", "quimica-organica.webp", "Química", "Ciências da Natureza", ["ENEM", "FUVEST"],
     "Aprenda funções orgânicas, reações e aplicações presentes no cotidiano.", "27.90", True, "Estudantes que buscam uma introdução objetiva à química orgânica para vestibulares."),
    ("historia-brasil", "História do Brasil em perspectiva", "andre", "historia-brasil.webp", "História", "Ciências Humanas", ["ENEM", "UNICAMP"],
     "Relacione os principais períodos da história brasileira a seus contextos sociais.", "0.00", True, "Estudantes que querem revisar História do Brasil conectando eventos e contextos."),
)

MECHANICS = (
    ("Grandezas e vetores", "Revise grandezas escalares, vetoriais e suas representações."),
    ("Movimento uniforme", "Entenda velocidade constante e interprete gráficos de movimento."),
    ("Movimento uniformemente variado", "Relacione aceleração, velocidade e posição em movimentos variados."),
    ("Queda livre", "Aplique as equações do movimento à queda dos corpos."),
    ("Lançamentos vertical e oblíquo", "Analise lançamentos decompondo o movimento em seus eixos."),
    ("Movimento e aceleração", "Consolide a relação entre movimento, velocidade e aceleração."),
    ("Introdução às forças", "Reconheça as principais forças presentes em problemas de mecânica."),
    ("Leis de Newton e suas aplicações", "Entenda as três leis de Newton e veja como elas ajudam a explicar situações do dia a dia."),
    ("Exercícios de dinâmica", "Resolva problemas de força resultante e movimento."),
    ("Trabalho e energia", "Relacione trabalho mecânico, energia e potência."),
    ("Impulso e quantidade de movimento", "Estude colisões, impulso e conservação da quantidade de movimento."),
    ("Revisão de mecânica", "Revise os conceitos do curso com questões de vestibular."),
)
QUANTUM = (
    ("Introdução e contexto histórico", "Conheça o contexto que levou ao surgimento da física quântica."),
    ("Radiação de corpo negro", "Entenda o problema da radiação de corpo negro e a quantização da energia."),
    ("Efeito fotoelétrico", "Relacione luz, frequência e emissão de elétrons."),
)
TOPICS = {
    "biologia-celular": (35, ("Tipos de célula", "Organelas", "Membrana plasmática", "Metabolismo", "Mitose e meiose", "Questões comentadas")),
    "estatistica-essencial": (28, ("Tabelas e gráficos", "Média, mediana e moda", "Dispersão", "Probabilidade básica", "Exercícios de prova")),
    "redacao-nota-mil": (20, ("Leitura do tema", "Tese e repertório", "Projeto de texto", "Desenvolvimento", "Conclusão", "Revisão orientada")),
    "quimica-organica": (31, ("Hidrocarbonetos", "Funções oxigenadas", "Funções nitrogenadas", "Principais mecanismos", "Polímeros", "Questões comentadas")),
    "historia-brasil": (26, ("Colonização", "Economia açucareira", "Mineração", "Império", "República", "Questões interdisciplinares")),
}
MODULES = {
    "fisica-quantica": (("Fundamentos", 3),),
    "fisica-enem-mecanica": (("Cinemática", 6), ("Dinâmica e energia", 6)),
    "biologia-celular": (("Estrutura celular", 3), ("Processos celulares", 3)),
    "estatistica-essencial": (("Leitura de dados", 2), ("Prática", 3)),
    "redacao-nota-mil": (("Planejamento", 3), ("Escrita", 3)),
    "quimica-organica": (("Funções orgânicas", 3), ("Reações", 3)),
    "historia-brasil": (("Brasil colonial", 3), ("Brasil contemporâneo", 3)),
}


def lessons_for(key):
    if key == "termodinamica":
        return []
    if key == "fisica-enem-mecanica":
        lessons = list(MECHANICS)
    elif key == "fisica-quantica":
        lessons = list(QUANTUM)
    else:
        count, topics = TOPICS[key]
        lessons = [(title, f"Aula demonstrativa: {title}.") for title in topics]
        lessons.extend((f"Prática e revisão {number:02} (demonstração)", "Exercícios demonstrativos para revisão.")
                       for number in range(1, count - len(topics) + 1))
    result = []
    for position, (title, description) in enumerate(lessons, 1):
        used = 0
        for section, size in MODULES[key]:
            used += size
            if position <= used:
                break
        else:
            section = "Prática e revisão"
        result.append((title, description, section))
    return result
