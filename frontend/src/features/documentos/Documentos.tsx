import { useState } from 'react'

import { useDocumentos, useFamilias, useRegistrarDocumento } from '../../api/queries'
import { Carregando, Erro, Vazio } from '../../components/Estado'
import { Etiqueta } from '../../components/Selo'
import { numero, rotuloFamilia } from '../../lib/formato'
import './Documentos.css'

export function Documentos() {
  const documentos = useDocumentos()
  const familias = useFamilias()

  const descobertas = (familias.data ?? []).filter((f) => f.e_problema && !f.coberta)
  const [familiaAlvo, setFamiliaAlvo] = useState<string | null>(null)

  return (
    <>
      <header className="pagina-cabecalho">
        <h1>Base documental</h1>
        <p>
          O sistema só recomenda o que consegue citar. Cada família de falha precisa de
          um procedimento indexado — sem ele, a análise entrega os dados e retém a
          recomendação.
        </p>
      </header>

      {descobertas.length > 0 && (
        <section className="painel lacunas">
          <div className="painel-corpo">
            <p className="rotulo">Famílias sem procedimento</p>
            <ul className="lacunas-lista">
              {descobertas.map((familia) => (
                <li key={familia.familia}>
                  <div>
                    <p className="lacunas-nome">{rotuloFamilia(familia.familia)}</p>
                    <p className="fraco">
                      {familia.descricao} · {numero(familia.eventos)} leituras
                    </p>
                  </div>
                  <button
                    type="button"
                    className="botao"
                    onClick={() => setFamiliaAlvo(familia.familia)}
                  >
                    Registrar procedimento
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </section>
      )}

      <Formulario
        familiaInicial={familiaAlvo}
        familias={(familias.data ?? []).filter((f) => f.e_problema).map((f) => f.familia)}
      />

      <section className="painel">
        <div className="painel-cabecalho">
          <h2>Documentos indexados</h2>
          <span className="fraco">extração e estado de cada arquivo</span>
        </div>
        <div className="painel-corpo painel-corpo--tabela">
          {documentos.isLoading && <Carregando altura="12rem" />}
          {documentos.isError && (
            <Erro erro={documentos.error} aoTentarNovamente={documentos.refetch} />
          )}
          {documentos.data?.length === 0 && (
            <Vazio titulo="Nenhum documento indexado">
              Rode <code className="dado">python manage.py ingest-docs</code> para
              carregar os procedimentos entregues pela empresa.
            </Vazio>
          )}
          {documentos.data && documentos.data.length > 0 && (
            <table>
              <thead>
                <tr>
                  <th>Arquivo</th>
                  <th>Título</th>
                  <th>Cobre</th>
                  <th className="num">Páginas</th>
                  <th className="num">Trechos</th>
                  <th>Extração</th>
                </tr>
              </thead>
              <tbody>
                {documentos.data.map((documento) => (
                  <tr key={documento.id}>
                    <td className="dado">{documento.arquivo}</td>
                    <td className="medio">{documento.titulo}</td>
                    <td>
                      {documento.familia ? (
                        <Etiqueta tom="ok">{rotuloFamilia(documento.familia)}</Etiqueta>
                      ) : (
                        <span className="fraco">—</span>
                      )}
                    </td>
                    <td className="num">{documento.paginas}</td>
                    <td className="num">{documento.trechos}</td>
                    <td>
                      {documento.metodo === 'ocr' ? (
                        <span
                          title={
                            'Páginas em imagem, transcritas automaticamente. ' +
                            'O texto pode divergir do original.'
                          }
                        >
                          <Etiqueta tom="atencao">
                            OCR
                            {documento.confianca_ocr !== null &&
                              ` · ${(documento.confianca_ocr * 100).toFixed(0)}%`}
                          </Etiqueta>
                        </span>
                      ) : (
                        <Etiqueta>camada de texto</Etiqueta>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </section>
    </>
  )
}

function Formulario({
  familiaInicial,
  familias,
}: {
  familiaInicial: string | null
  familias: string[]
}) {
  const registrar = useRegistrarDocumento()
  const [arquivo, setArquivo] = useState<File | null>(null)
  const [titulo, setTitulo] = useState('')
  const [familia, setFamilia] = useState('')

  const escolhida = familia || familiaInicial || ''

  function enviar(evento: React.FormEvent) {
    evento.preventDefault()
    if (!arquivo || !escolhida) return
    registrar.mutate(
      { arquivo, familia: escolhida, titulo: titulo || arquivo.name },
      {
        onSuccess: () => {
          setArquivo(null)
          setTitulo('')
        },
      },
    )
  }

  return (
    <section className="painel">
      <div className="painel-cabecalho">
        <h2>Registrar novo procedimento</h2>
        <span className="fraco">PDF · até 20 MB</span>
      </div>

      <form className="painel-corpo formulario" onSubmit={enviar}>
        <label className="campo">
          <span className="rotulo">Arquivo</span>
          <input
            type="file"
            accept="application/pdf"
            onChange={(e) => setArquivo(e.target.files?.[0] ?? null)}
          />
          <span className="campo-dica fraco">
            PDF sem camada de texto passa por OCR automaticamente.
          </span>
        </label>

        <label className="campo">
          <span className="rotulo">Falha que o documento cobre</span>
          <select value={escolhida} onChange={(e) => setFamilia(e.target.value)} required>
            <option value="">Escolha a família</option>
            {familias.map((nome) => (
              <option key={nome} value={nome}>
                {rotuloFamilia(nome)}
              </option>
            ))}
          </select>
          <span className="campo-dica fraco">
            Informada por quem registra, nunca deduzida pelo modelo.
          </span>
        </label>

        <label className="campo">
          <span className="rotulo">Título</span>
          <input
            value={titulo}
            onChange={(e) => setTitulo(e.target.value)}
            placeholder={arquivo?.name ?? 'Procedimento de…'}
          />
        </label>

        <div className="formulario-acoes">
          <button
            type="submit"
            className="botao botao-primario"
            disabled={!arquivo || !escolhida || registrar.isPending}
          >
            {registrar.isPending ? 'Processando…' : 'Registrar'}
          </button>

          {registrar.isPending && (
            <span className="fraco">
              Extraindo texto, dividindo em trechos e gerando embeddings.
            </span>
          )}

          {registrar.isError && (
            <span className="formulario-erro">
              {(registrar.error as Error).message}
            </span>
          )}

          {registrar.isSuccess && (
            <span className="formulario-ok">
              {registrar.data.ja_existia && !registrar.data.cobertura_atualizada
                ? 'Documento já estava indexado para esta família.'
                : `Indexado: ${registrar.data.trechos} trechos, ${registrar.data.paginas} páginas.
                   A família passa a receber recomendação.`}
            </span>
          )}
        </div>
      </form>
    </section>
  )
}
