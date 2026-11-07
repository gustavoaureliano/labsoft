"""Full browser-demo catalog. No persistence or real enrollment implementation."""

from dataclasses import replace

from app.integrations import Course, CourseSection, DemoIntegrations, User

MECHANICS = [
    ("grandezas-vetores", "Grandezas e vetores"),
    ("movimento-uniforme", "Movimento uniforme"),
    ("movimento-variado", "Movimento uniformemente variado"),
    ("queda-livre", "Queda livre"),
    ("lancamentos", "Lançamentos vertical e oblíquo"),
    ("movimento-aceleracao", "Movimento e aceleração"),
    ("introducao-forcas", "Introdução às forças"),
    ("leis-newton", "Leis de Newton e suas aplicações"),
    ("exercicios-dinamica", "Exercícios de dinâmica"),
    ("trabalho-energia", "Trabalho e energia"),
    ("impulso-quantidade", "Impulso e quantidade de movimento"),
    ("revisao-mecanica", "Revisão de mecânica"),
]

LESSONS = {
    "fisica-enem-mecanica": MECHANICS,
    "fisica-quantica": [("q1", "Introdução e contexto histórico"), ("q2", "Radiação de corpo negro"), ("q3", "Efeito fotoelétrico")],
}

# Courses that previously had only counts/syllabi receive explicitly fictitious
# practice lessons after their introductory topics, matching the advertised count.
TOPICS = {
    "biologia-celular": (35, ["Tipos de célula", "Organelas", "Membrana plasmática", "Metabolismo", "Mitose e meiose", "Questões comentadas"]),
    "estatistica-essencial": (28, ["Tabelas e gráficos", "Média, mediana e moda", "Dispersão", "Probabilidade básica", "Exercícios de prova"]),
    "redacao-nota-mil": (20, ["Leitura do tema", "Tese e repertório", "Projeto de texto", "Desenvolvimento", "Conclusão", "Revisão orientada"]),
    "quimica-organica": (31, ["Hidrocarbonetos", "Funções oxigenadas", "Funções nitrogenadas", "Principais mecanismos", "Polímeros", "Questões comentadas"]),
    "historia-brasil": (26, ["Colonização", "Economia açucareira", "Mineração", "Império", "República", "Questões interdisciplinares"]),
}
for course_id, (count, topics) in TOPICS.items():
    LESSONS[course_id] = [
        (f"{course_id}-aula-{index + 1:02}", topics[index] if index < len(topics) else f"Prática e revisão {index - len(topics) + 1:02} (demonstração)")
        for index in range(count)
    ]


MODULES = {
    "fisica-enem-mecanica": (("Cinemática", 6), ("Dinâmica e energia", 6)),
    "fisica-quantica": (("Fundamentos", 3),),
    "biologia-celular": (("Estrutura celular", 3), ("Processos celulares", 3)),
    "estatistica-essencial": (("Leitura de dados", 2), ("Prática", 3)),
    "redacao-nota-mil": (("Planejamento", 3), ("Escrita", 3)),
    "quimica-organica": (("Funções orgânicas", 3), ("Reações", 3)),
    "historia-brasil": (("Brasil colonial", 3), ("Brasil contemporâneo", 3)),
}


def showcase_sections(course_id: str) -> tuple[CourseSection, ...]:
    lessons = LESSONS[course_id]
    sections = []
    position = 0
    for title, count in MODULES[course_id]:
        sections.append(CourseSection(title, tuple(id for id, _ in lessons[position:position + count])))
        position += count
    if position < len(lessons):
        sections.append(CourseSection("Prática e revisão", tuple(id for id, _ in lessons[position:])))
    return tuple(sections)


class ShowcaseIntegrations(DemoIntegrations):
    users = {
        **DemoIntegrations.users,
        "professor-estatistica": User("professor-estatistica", "teacher", "Prof. Rafael Costa"),
        "professora-redacao": User("professora-redacao", "teacher", "Profa. Marina Lopes"),
        "professor-quimica": User("professor-quimica", "teacher", "Prof. Lucas Ribeiro"),
        "professor-historia": User("professor-historia", "teacher", "Prof. André Nascimento"),
    }
    catalog = {
        **DemoIntegrations.catalog,
        "biologia-celular": Course("biologia-celular", "Biologia Celular para Vestibulares", "professor-demo-2", "/images/courses/biologia-celular.webp", "Dra. Clara Mendonça"),
        "estatistica-essencial": Course("estatistica-essencial", "Estatística Essencial", "professor-estatistica", "/images/courses/estatistica.webp", "Prof. Rafael Costa"),
        "redacao-nota-mil": Course("redacao-nota-mil", "Redação nota mil: da tese à conclusão", "professora-redacao", "/images/courses/redacao-nota-mil.webp", "Profa. Marina Lopes"),
        "quimica-organica": Course("quimica-organica", "Química Orgânica sem mistério", "professor-quimica", "/images/courses/quimica-organica.webp", "Prof. Lucas Ribeiro"),
        "historia-brasil": Course("historia-brasil", "História do Brasil em perspectiva", "professor-historia", "/images/courses/historia-brasil.webp", "Prof. André Nascimento"),
        "termodinamica": Course("termodinamica", "Termodinâmica Avançada", "professor-demo", "/teacher-thermo.png", "Prof. Fulano da Silva", published=False),
    }
    catalog = {id: replace(course, sections=showcase_sections(id)) if id in MODULES else course for id, course in catalog.items()}

    def has_access(self, student_id: str, course_id: str) -> bool:
        course = self.course(course_id)
        if student_id == "aluno-demo":
            return bool(course and course.published)
        return super().has_access(student_id, course_id)

    def recommendations(self, student_id: str) -> list[Course]:
        return []  # Main showcase student already has access to all published courses.
