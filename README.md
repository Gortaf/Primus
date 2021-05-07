# Primus

## Qu'est ce que Primus?
Primus est un petit logiciel Python qui a pour but d'aider les étudiants à l'Université de Montréal en determinant quels cours ne sont pas en conflits d'horaires avec ceux auxquels ils sont déjà inscrits en analysant synchro.

**La version .exe de Primus est disponible sur ce [lien](https://drive.google.com/file/d/1CXgFEWL1gPFTJxtJu-YBXjaYgFTrHAlK/view?usp=sharing).**
**FireFox doit être installé pour que Primus fonctionne**

## Comment ça marche?
#### Point de vu utilisateur
D'un point de vu utilisateur, il suffit d'executer Primus.exe. Primus offre une interface graphique facile à utiliser. Au lancement, cette interface (ainsi qu'une console) seront affichés. Il suffit de rentrer les creditentiels synchro et d'appuyer sur "Commencer" (Primus supprime ces creditentiels de sa mémoire immediatement après les avoir envoyés à synchro). Puis une fois que la liste des sessions est disponible, choisir la session sur laquelle Primus doit travailler à l'aide du menu déroulant, puis cliquer sur "Selectionner". Primus débutera sa séquence principale, et si tout se passe bien, les cours traités seront affichés au fur et à mesure dans les espaces dédiés à droites. Il y a 3 espaces differents, chacun correspondants à des situations differentes indentifiés pour un cours:
- **Valide** (en vert): Les cours dans cet espace n'ont aucun conflit d'horaire avec votre emploi du temps actuel
- **Invalide** (en rouge): Il est impossible de prendre les cours dans cette section sans générer de conflits d'horaire avec votre emploi du temps actuel
- **Inconnues** (en orange): Primus ne peut pas être certain de la validité de ces cours. Souvent générés quand un cours à des horaires "à communiqué". Il est possible, voir probable que certains de ces cours soit valide;

#### Point de vu technique
D'un point de vu technique, Primus s'appuis sur Selenium pour émuler des navigateurs et récupérer les données nescessaires depuis le centre étudiant. Plusieurs navigateurs sont générés, et les opérations de ces derniers sont répartis sur plusieurs threads pour pouvoir examiner plusieurs cours de manière parallèles (très utile étant donné la lenteur de synchro...). Chaque thread se voit attribué un "bloc" de cours à examiner sur synchro, et va aller récuperer les données de ce cours. Une fois les données acquises, la thread démarre une autre thread (I know it's confusing...) qui va s'occuper de determiner la compatibilité du cours, ce afin de ne pas ralentir les threads s'occupant de naviguer synchro. Pour determinre la compatibilité, il faut que au moins une combinaison de sections (TH/TP/LAB/etc...) soit compatible avec l'emploi du temps "root". Pour ce faire, un genre d'arbre est utilisé. Cette structure permet de facilement determiner si au moins une combinaison est valide, et remonter ces combinaisons valides pour verifier qu'au moins une ne comprends pas de sections "inconnues" (auquel cas le cours finira dans les cours "inconnus"). Primus à ensuite été wrappé dans un .exe à l'aide de pyinstaller avec la commande suivante: `pyinstaller --onefile --name Primus --icon=logo.ico Interface.py`

## À Propos:
Primus est un "successeur" à ClassFinder, un autre projet que j'avais fait durant ma première année avec le même but en tête. Primus est plus maintenable en terme de programmation, utilise des "webscrapping hooks" plus robustes et à jours sur le centre étudiant, à une manière de determiner la validité d'un cours **beaucoup** robuste, et utilise le multithreading pour réduire le temps d'execution.
Le nom "Primus" vient de Donjons & Dragons. Primus est le chef des modrons sur le plan de l'ordre "Mechanus". Son but est de transformer le chaos en ordre, tout comme le but de ce logiciel est de transformer le chaos de synchro en un semblant d'ordre.
