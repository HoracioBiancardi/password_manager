"""Interface de linha de comando do gerenciador de senhas."""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from password_manager.config import CAMINHO_ENV, Settings
from password_manager.crypto.crypto_service import CryptoService
from password_manager.exceptions import ChaveMestreInvalidaError
from password_manager.models.credencial import Credencial
from password_manager.services.password_manager_service import PasswordManagerService
from password_manager.storage.file_storage import FileStorage

app = typer.Typer(
    name="pm",
    help="Gerenciador de senhas seguro com criptografia Fernet.",
    no_args_is_help=True,
)
console = Console()

_CAMINHO_PADRAO: Path = Path(".password-manager") / "senhas.enc"


def _obter_chave_mestre() -> str:
    """Retorna a chave mestre do .env se disponível, caso contrário solicita via prompt.

    Returns:
        String da chave mestre Fernet.
    """
    settings = Settings()
    if settings.master_key:
        console.print("[dim]Chave Mestre carregada do .env[/dim]")
        return settings.master_key
    return typer.prompt("Chave Mestre", hide_input=True)


def _salvar_chave_no_env(chave: str) -> None:
    """Cria ou atualiza MASTER_KEY no arquivo .env.

    Preserva outras variáveis existentes no arquivo.

    Args:
        chave: Chave Fernet a persistir.
    """
    CAMINHO_ENV.parent.mkdir(parents=True, exist_ok=True)
    linhas = CAMINHO_ENV.read_text(encoding="utf-8").splitlines() if CAMINHO_ENV.exists() else []
    nova_linha = f"MASTER_KEY={chave}"
    novas_linhas = [
        nova_linha if linha.startswith("MASTER_KEY=") else linha
        for linha in linhas
    ]
    if not any(linha.startswith("MASTER_KEY=") for linha in linhas):
        novas_linhas.append(nova_linha)
    CAMINHO_ENV.write_text("\n".join(novas_linhas) + "\n", encoding="utf-8")


def _criar_servico(chave_mestre: str, caminho: Path) -> PasswordManagerService:
    """Fábrica que instancia e injeta as dependências do serviço principal.

    Args:
        chave_mestre: Chave Fernet do usuário.
        caminho: Caminho para o arquivo de dados criptografados.

    Returns:
        PasswordManagerService configurado e pronto para uso.

    Raises:
        ChaveMestreInvalidaError: Se o formato da chave for inválido.
    """
    caminho.parent.mkdir(parents=True, exist_ok=True)
    return PasswordManagerService(
        crypto=CryptoService(chave_mestre),
        storage=FileStorage(caminho),
    )


@app.command()
def gerar_chave(
    salvar: bool = typer.Option(
        False, "--salvar", "-s", help=f"Salva a chave no {CAMINHO_ENV} automaticamente."
    ),
) -> None:
    """Gera e exibe uma nova Chave Mestre Fernet para primeiro uso."""
    chave: str = CryptoService.gerar_nova_chave()
    console.print("\n[bold green]Nova Chave Mestre gerada:[/bold green]")
    console.print(f"\n  [bold yellow]{chave}[/bold yellow]\n")

    if salvar:
        _salvar_chave_no_env(chave)
        console.print(f"[green]✓[/green] Chave salva em [dim]{CAMINHO_ENV}[/dim]")
        console.print("[dim]Certifique-se de que este arquivo não seja versionado (adicione ao .gitignore).[/dim]\n")
    else:
        console.print("[bold red]ATENÇÃO:[/bold red] Guarde esta chave em local seguro.")
        console.print("Sem ela, suas senhas [bold]não poderão ser recuperadas[/bold].")
        console.print(f"\n[dim]Dica: use [bold]pm gerar-chave --salvar[/bold] para salvar no .env automaticamente.[/dim]\n")


@app.command()
def adicionar(
    arquivo: Path = typer.Option(
        _CAMINHO_PADRAO, "--arquivo", "-a", help="Caminho do arquivo de senhas."
    ),
) -> None:
    """Adiciona uma nova credencial ao cofre criptografado."""
    console.print("\n[bold]--- Adicionar Nova Credencial ---[/bold]\n")
    nome: str = typer.prompt("Serviço")
    url: str = typer.prompt("URL do Serviço (Enter para pular)", default="")
    email: str = typer.prompt("E-mail ou Usuário")
    senha: str = typer.prompt("Senha", hide_input=True, confirmation_prompt=True)
    observacao: str = typer.prompt("Observação (Enter para pular)", default="")
    chave_mestre: str = _obter_chave_mestre()

    try:
        servico: PasswordManagerService = _criar_servico(chave_mestre, arquivo)
        servico.adicionar_credencial(Credencial(nome=nome, url=url, email=email, senha=senha, observacao=observacao))
        console.print(f"\n[green]✓[/green] Credencial '[bold]{nome}[/bold]' adicionada com sucesso.\n")
    except ChaveMestreInvalidaError as exc:
        console.print(f"\n[bold red]✗ Erro:[/bold red] {exc}\n")
        raise typer.Exit(1)


@app.command()
def buscar(
    termo: str = typer.Argument(..., help="Nome do serviço ou e-mail a buscar."),
    arquivo: Path = typer.Option(
        _CAMINHO_PADRAO, "--arquivo", "-a", help="Caminho do arquivo de senhas."
    ),
) -> None:
    """Busca e exibe credenciais completas (incluindo senha) por nome ou e-mail."""
    console.print(f"\n[dim]Buscando por:[/dim] '{termo}'")
    chave_mestre: str = _obter_chave_mestre()

    try:
        servico: PasswordManagerService = _criar_servico(chave_mestre, arquivo)
        resultados: list[Credencial] = servico.buscar_credenciais(termo)
    except ChaveMestreInvalidaError as exc:
        console.print(f"\n[bold red]✗ Erro:[/bold red] {exc}\n")
        raise typer.Exit(1)

    if not resultados:
        console.print(f"\n[yellow]Nenhuma credencial encontrada para '{termo}'.[/yellow]\n")
        return

    tabela = Table(title=f"Resultados para '{termo}'", show_lines=True)
    tabela.add_column("Serviço", style="cyan", no_wrap=True)
    tabela.add_column("URL", style="blue")
    tabela.add_column("E-mail/Usuário", style="magenta")
    tabela.add_column("Senha", style="green")
    tabela.add_column("Observação", style="white")
    for cred in resultados:
        tabela.add_row(cred.nome, cred.url, cred.email, cred.senha, cred.observacao)

    console.print()
    console.print(tabela)
    console.print()


@app.command()
def atualizar(
    termo: str = typer.Argument(..., help="Nome do serviço a atualizar."),
    arquivo: Path = typer.Option(
        _CAMINHO_PADRAO, "--arquivo", "-a", help="Caminho do arquivo de senhas."
    ),
) -> None:
    """Atualiza os dados de uma credencial existente (Enter mantém o valor atual)."""
    chave_mestre: str = _obter_chave_mestre()

    try:
        servico: PasswordManagerService = _criar_servico(chave_mestre, arquivo)
        correspondencias: list[Credencial] = servico.buscar_credenciais(termo)
    except ChaveMestreInvalidaError as exc:
        console.print(f"\n[bold red]✗ Erro:[/bold red] {exc}\n")
        raise typer.Exit(1)

    if not correspondencias:
        console.print(f"\n[yellow]Nenhuma credencial encontrada para '{termo}'.[/yellow]\n")
        return

    if len(correspondencias) > 1:
        tabela = Table(title=f"Múltiplas correspondências para '{termo}'", show_lines=True)
        tabela.add_column("#", style="dim", width=3)
        tabela.add_column("Serviço", style="cyan")
        tabela.add_column("URL", style="blue")
        tabela.add_column("E-mail/Usuário", style="magenta")
        for i, cred in enumerate(correspondencias, start=1):
            tabela.add_row(str(i), cred.nome, cred.url, cred.email)
        console.print()
        console.print(tabela)

        escolha: int = typer.prompt("Número da credencial a atualizar", type=int)
        if not 1 <= escolha <= len(correspondencias):
            console.print("[red]Número inválido.[/red]\n")
            raise typer.Exit(1)
        alvo: Credencial = correspondencias[escolha - 1]
    else:
        alvo = correspondencias[0]

    console.print(f"\n[bold]Atualizando:[/bold] {alvo.nome}")
    console.print("[dim](Enter para manter o valor atual)[/dim]\n")

    novo_nome: str = typer.prompt("Serviço", default=alvo.nome)
    nova_url: str = typer.prompt("URL do Serviço", default=alvo.url)
    novo_email: str = typer.prompt("E-mail ou Usuário", default=alvo.email)
    nova_observacao: str = typer.prompt("Observação", default=alvo.observacao)

    if typer.confirm("Alterar senha?", default=False):
        nova_senha: str = typer.prompt("Nova Senha", hide_input=True, confirmation_prompt=True)
    else:
        nova_senha = alvo.senha

    nova = Credencial(nome=novo_nome, url=nova_url, email=novo_email, senha=nova_senha, observacao=nova_observacao)

    if servico.atualizar_credencial(alvo.nome, alvo.email, nova):
        console.print(f"\n[green]✓[/green] Credencial '[bold]{novo_nome}[/bold]' atualizada.\n")
    else:
        console.print("\n[red]✗[/red] Não foi possível atualizar a credencial.\n")


@app.command()
def listar(
    arquivo: Path = typer.Option(
        _CAMINHO_PADRAO, "--arquivo", "-a", help="Caminho do arquivo de senhas."
    ),
) -> None:
    """Lista todos os serviços e e-mails armazenados (senhas omitidas)."""
    chave_mestre: str = _obter_chave_mestre()

    try:
        servico: PasswordManagerService = _criar_servico(chave_mestre, arquivo)
        credenciais: list[Credencial] = servico.listar_credenciais()
    except ChaveMestreInvalidaError as exc:
        console.print(f"\n[bold red]✗ Erro:[/bold red] {exc}\n")
        raise typer.Exit(1)

    if not credenciais:
        console.print("\n[yellow]Nenhuma credencial cadastrada.[/yellow]\n")
        return

    tabela = Table(title="Credenciais Armazenadas", show_lines=True)
    tabela.add_column("#", style="dim", width=3)
    tabela.add_column("Serviço", style="cyan")
    tabela.add_column("URL", style="blue")
    tabela.add_column("E-mail/Usuário", style="magenta")
    for i, cred in enumerate(credenciais, start=1):
        tabela.add_row(str(i), cred.nome, cred.url, cred.email)

    console.print()
    console.print(tabela)
    console.print()


@app.command()
def remover(
    nome: str = typer.Argument(..., help="Nome do serviço a remover."),
    arquivo: Path = typer.Option(
        _CAMINHO_PADRAO, "--arquivo", "-a", help="Caminho do arquivo de senhas."
    ),
) -> None:
    """Remove uma credencial pelo nome do serviço."""
    chave_mestre: str = _obter_chave_mestre()

    try:
        servico: PasswordManagerService = _criar_servico(chave_mestre, arquivo)
        correspondencias: list[Credencial] = servico.buscar_credenciais(nome)
    except ChaveMestreInvalidaError as exc:
        console.print(f"\n[bold red]✗ Erro:[/bold red] {exc}\n")
        raise typer.Exit(1)

    if not correspondencias:
        console.print(f"\n[yellow]Nenhuma credencial encontrada para '{nome}'.[/yellow]\n")
        return

    if len(correspondencias) > 1:
        tabela = Table(title=f"Múltiplas correspondências para '{nome}'", show_lines=True)
        tabela.add_column("#", style="dim", width=3)
        tabela.add_column("Serviço", style="cyan")
        tabela.add_column("E-mail/Usuário", style="magenta")
        for i, cred in enumerate(correspondencias, start=1):
            tabela.add_row(str(i), cred.nome, cred.email)
        console.print()
        console.print(tabela)

        escolha: int = typer.prompt("Número da credencial a remover", type=int)
        if not 1 <= escolha <= len(correspondencias):
            console.print("[red]Número inválido.[/red]\n")
            raise typer.Exit(1)
        alvo: Credencial = correspondencias[escolha - 1]
    else:
        alvo = correspondencias[0]
        if not typer.confirm(f"Remover '{alvo.nome}' ({alvo.email})?"):
            console.print("[yellow]Operação cancelada.[/yellow]\n")
            return

    if servico.remover_credencial(alvo.nome, alvo.email):
        console.print(f"\n[green]✓[/green] Credencial '[bold]{alvo.nome}[/bold]' removida.\n")
    else:
        console.print("\n[red]✗[/red] Não foi possível remover a credencial.\n")
