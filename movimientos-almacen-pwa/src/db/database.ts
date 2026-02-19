import Dexie from "dexie";

export type MovementType = {
  id?: number;
  name: string;
  createdAt: string;
};

export type Movement = {
  id?: number;
  movementTypeId: number;
  movementName: string;
  comment: string;
  ts: string;
  hhmmss: string;
  dayKey: string;
};

class AppDB extends Dexie {
  movementTypes!: Dexie.Table<MovementType, number>;
  movements!: Dexie.Table<Movement, number>;

  constructor() {
    super("movimientos_almacen_db");
    this.version(1).stores({
      movementTypes: "++id, name, createdAt",
      movements: "++id, movementTypeId, dayKey, ts",
    });
  }
}

export const db = new AppDB();

export function nowLocalStamp() {
  const now = new Date();
  const hh = String(now.getHours()).padStart(2, "0");
  const mm = String(now.getMinutes()).padStart(2, "0");
  const ss = String(now.getSeconds()).padStart(2, "0");

  const yyyy = now.getFullYear();
  const mo = String(now.getMonth() + 1).padStart(2, "0");
  const dd = String(now.getDate()).padStart(2, "0");

  return {
    ts: now.toISOString(),
    hhmmss: `${hh}:${mm}:${ss}`,
    dayKey: `${yyyy}-${mo}-${dd}`,
  };
}

export function isDistCar(name: string) {
  return name.trim().toLowerCase() === "dist. car.".toLowerCase();
}
