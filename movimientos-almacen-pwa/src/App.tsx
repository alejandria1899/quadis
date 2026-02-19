import { useEffect, useMemo, useState } from "react";
import "./App.css";
import { db, isDistCar, nowLocalStamp } from "./db/database";
import type { Movement, MovementType } from "./db/database";
import jsPDF from "jspdf";

type Screen = "home" | "comment" | "manage" | "history" | "edit" | "pdf";

export default function App() {
  const [screen, setScreen] = useState<Screen>("home");

  const [types, setTypes] = useState<MovementType[]>([]);
  const [movements, setMovements] = useState<Movement[]>([]);

  const [selectedType, setSelectedType] = useState<MovementType | null>(null);
  const [comment, setComment] = useState("");

  // Dist. car extras
  const [carro, setCarro] = useState<number | null>(null);
  const [zona, setZona] = useState<number | null>(null);

  // Edit
  const [editId, setEditId] = useState<number | null>(null);
  const [editName, setEditName] = useState("");
  const [editComment, setEditComment] = useState("");

  // PDF day
  const [pdfDay, setPdfDay] = useState(() => {
    const d = new Date();
    const yyyy = d.getFullYear();
    const mo = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    return `${yyyy}-${mo}-${dd}`;
  });

  async function refresh() {
    const t = await db.movementTypes.orderBy("name").toArray();
    setTypes(t);

    const m = await db.movements.orderBy("id").reverse().limit(80).toArray();
    setMovements(m);
  }

  useEffect(() => {
    refresh();
  }, []);

  function go(next: Screen) {
    setScreen(next);
  }

  // --- Actions ---
  async function addType(name: string) {
    const trimmed = name.trim();
    if (!trimmed) return;

    // evita duplicados por nombre
    const exists = await db.movementTypes.where("name").equals(trimmed).first();
    if (exists) return;

    await db.movementTypes.add({ name: trimmed, createdAt: new Date().toISOString() });
    await refresh();
  }

  async function deleteType(id?: number) {
    if (!id) return;
    await db.movementTypes.delete(id);
    await refresh();
  }

  async function createMovement() {
    if (!selectedType?.id) return;

    const stamp = nowLocalStamp();

    let finalComment = comment.trim();
    if (selectedType && isDistCar(selectedType.name)) {
      const parts: string[] = [];
      if (carro) parts.push(`Carro:${carro}`);
      if (zona) parts.push(`Zona:${zona}`);
      if (parts.length) {
        const prefix = parts.join(" ");
        finalComment = finalComment ? `${prefix} - ${finalComment}` : prefix;
      }
    }

    await db.movements.add({
      movementTypeId: selectedType.id,
      movementName: selectedType.name,
      comment: finalComment,
      ts: stamp.ts,
      hhmmss: stamp.hhmmss,
      dayKey: stamp.dayKey,
    });

    // reset
    setSelectedType(null);
    setComment("");
    setCarro(null);
    setZona(null);

    await refresh();
    go("home");
  }

  async function deleteMovement(id?: number) {
    if (!id) return;
    await db.movements.delete(id);
    await refresh();
  }

  async function openEdit(m: Movement) {
    setEditId(m.id ?? null);
    setEditName(m.movementName);
    setEditComment(m.comment);
    go("edit");
  }

  async function saveEdit() {
    if (!editId) return;
    await db.movements.update(editId, {
      movementName: editName.trim() || "Sin nombre",
      comment: editComment.trim(),
    });
    setEditId(null);
    setEditName("");
    setEditComment("");
    await refresh();
    go("history");
  }

  async function exportPdfForDay(dayKey: string) {
    const rows = await db.movements.where("dayKey").equals(dayKey).toArray();
    rows.sort((a, b) => (a.id ?? 0) - (b.id ?? 0));

    const doc = new jsPDF();
    doc.setFontSize(14);
    doc.text(`Registro de movimientos - ${dayKey}`, 10, 12);

    doc.setFontSize(10);
    let y = 22;

    doc.text("Hora", 10, y);
    doc.text("Movimiento", 30, y);
    doc.text("Comentario", 90, y);
    y += 6;

    doc.line(10, y, 200, y);
    y += 6;

    const maxComment = 60;

    for (const r of rows) {
      if (y > 285) {
        doc.addPage();
        y = 20;
      }
      const comment = (r.comment || "").length > maxComment
        ? (r.comment || "").slice(0, maxComment - 3) + "..."
        : (r.comment || "");

      doc.text(r.hhmmss, 10, y);
      doc.text((r.movementName || "").slice(0, 28), 30, y);
      doc.text(comment, 90, y);
      y += 6;
    }

    doc.save(`movimientos_${dayKey}.pdf`);
  }

  // UI helpers
  const carros = useMemo(() => Array.from({ length: 26 }, (_, i) => i + 1), []);
  const zonas = useMemo(() => Array.from({ length: 11 }, (_, i) => i + 1), []);

  // ---------------- UI ----------------
  return (
    <div className="app">
      <header className="topbar">
        <div className="title">📦 Movimientos (pistola)</div>
        <div className="nav">
          <button className={screen === "home" ? "active" : ""} onClick={() => go("home")}>Movimientos</button>
          <button className={screen === "manage" ? "active" : ""} onClick={() => go("manage")}>Botones</button>
          <button className={screen === "history" ? "active" : ""} onClick={() => go("history")}>Historial</button>
          <button className={screen === "pdf" ? "active" : ""} onClick={() => go("pdf")}>PDF</button>
        </div>
      </header>

      {screen === "home" && (
        <main>
          <h2>Toca un botón para registrar</h2>

          {types.length === 0 ? (
            <div className="card">
              No tienes botones. Ve a <b>Botones</b> para crear el primero.
            </div>
          ) : (
            <div className="grid">
              {types.map((t) => (
                <button
                  key={t.id}
                  className="tile"
                  onClick={() => {
                    setSelectedType(t);
                    setComment("");
                    setCarro(null);
                    setZona(null);
                    go("comment");
                  }}
                  title={t.name}
                >
                  {t.name}
                </button>
              ))}
            </div>
          )}
        </main>
      )}

      {screen === "comment" && selectedType && (
        <main>
          <h2>Comentario: {selectedType.name}</h2>

          {isDistCar(selectedType.name) && (
            <div className="card">
              <div className="subtitle">Dist. car. — Selecciona Carro y Zona</div>

              <div className="section">
                <div className="label">Carro (1–26)</div>
                <div className="miniGrid">
                  {carros.map((n) => (
                    <button
                      key={n}
                      className={"miniBtn" + (carro === n ? " miniActive" : "")}
                      onClick={() => setCarro(n)}
                    >
                      {n}
                    </button>
                  ))}
                </div>
              </div>

              <div className="section">
                <div className="label">Zona (1–11)</div>
                <div className="miniGrid">
                  {zonas.map((z) => (
                    <button
                      key={z}
                      className={"miniBtn" + (zona === z ? " miniActive" : "")}
                      onClick={() => setZona(z)}
                    >
                      {z}
                    </button>
                  ))}
                </div>
              </div>

              <div className="hint">
                Seleccionado → Carro: <b>{carro ?? "-"}</b> | Zona: <b>{zona ?? "-"}</b>
              </div>
            </div>
          )}

          <textarea
            className="textarea"
            placeholder="Comentario (opcional). Ej: Ubicación A-12, caja dañada..."
            value={comment}
            onChange={(e) => setComment(e.target.value)}
          />

          <div className="row">
            <button className="primary" onClick={createMovement}>Guardar</button>
            <button
              onClick={() => {
                setSelectedType(null);
                setComment("");
                setCarro(null);
                setZona(null);
                go("home");
              }}
            >
              Cancelar
            </button>
          </div>
        </main>
      )}

      {screen === "manage" && (
        <main>
          <h2>Botones</h2>

          <div className="card">
            <div className="label">Crear botón</div>
            <TypeCreate onCreate={addType} />
          </div>

          <div className="card">
            <div className="label">Eliminar botón</div>
            {types.length === 0 ? (
              <div className="muted">No hay botones.</div>
            ) : (
              <div className="list">
                {types.map((t) => (
                  <div className="listRow" key={t.id}>
                    <div className="listText">{t.name}</div>
                    <button className="danger" onClick={() => deleteType(t.id)}>Borrar</button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </main>
      )}

      {screen === "history" && (
        <main>
          <h2>Historial</h2>

          {movements.length === 0 ? (
            <div className="card">Aún no has registrado movimientos.</div>
          ) : (
            <div className="card">
              <div className="list">
                {movements.map((m) => (
                  <div className="movRow" key={m.id}>
                    <div className="movMain">
                      <div className="movTitle">
                        <span className="time">{m.hhmmss}</span> — {m.movementName}
                      </div>
                      <div className="movComment">{m.comment || "—"}</div>
                    </div>
                    <div className="movActions">
                      <button onClick={() => openEdit(m)}>Editar</button>
                      <button className="danger" onClick={() => deleteMovement(m.id)}>Eliminar</button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </main>
      )}

      {screen === "edit" && editId && (
        <main>
          <h2>Editar movimiento</h2>

          <div className="card">
            <div className="label">Nombre</div>
            <input className="input" value={editName} onChange={(e) => setEditName(e.target.value)} />
            <div className="label" style={{ marginTop: 10 }}>Comentario</div>
            <textarea className="textarea" value={editComment} onChange={(e) => setEditComment(e.target.value)} />
            <div className="row">
              <button className="primary" onClick={saveEdit}>Guardar cambios</button>
              <button onClick={() => go("history")}>Cancelar</button>
            </div>
          </div>
        </main>
      )}

      {screen === "pdf" && (
        <main>
          <h2>Exportar PDF</h2>

          <div className="card">
            <div className="label">Día</div>
            <input
              className="input"
              type="date"
              value={pdfDay}
              onChange={(e) => setPdfDay(e.target.value)}
            />
            <div className="row">
              <button className="primary" onClick={() => exportPdfForDay(pdfDay)}>Descargar PDF</button>
            </div>
            <div className="muted">Funciona offline. El PDF se genera en tu móvil.</div>
          </div>
        </main>
      )}
    </div>
  );
}

function TypeCreate({ onCreate }: { onCreate: (name: string) => Promise<void> }) {
  const [value, setValue] = useState("");

  return (
    <div className="row">
      <input
        className="input"
        placeholder='Ej: "Dist. car." / "Entradas" / "Inv"...'
        value={value}
        onChange={(e) => setValue(e.target.value)}
      />
      <button
        className="primary"
        onClick={async () => {
          await onCreate(value);
          setValue("");
        }}
      >
        Crear
      </button>
    </div>
  );
}
