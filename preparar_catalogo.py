import json
import re
import unicodedata
import numpy as np
import pandas as pd


def to_slug(text):
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


SPECIES_MAP = {
    "bovinos": "bovinos",
    "equinos": "equinos",
    "porcinos": "porcinos",
    "caprinos": "caprinos",
    "ovinos": "ovinos",
    "aviar": "aviar",
    "aves": "aviar",
    "canino": "canino",
    "caninos": "canino",
    "perros": "canino",
    "felino": "felino",
    "felinos": "felino",
    "gatos": "felino",
    "aquacultura": "aquacultura",
    "apicola": "apicola",
    "apícola": "apicola",
    "roedores": "roedores",
    "reptilia": "reptilia",
    "cunicos": "cunicos",
    "cúnicos": "cunicos",
    "aves ornamentales": "aves-ornamentales",
}


def map_species(raw):
    if pd.isna(raw) or not str(raw).strip():
        return []
    parts = re.split(r"[,|;/]+", str(raw))
    slugs = []
    for p in parts:
        clean = p.strip().lower()
        clean_no_acc = "".join(
            ch for ch in unicodedata.normalize("NFD", clean) if unicodedata.category(ch) != "Mn"
        )
        slug = SPECIES_MAP.get(clean) or SPECIES_MAP.get(clean_no_acc) or to_slug(clean)
        if slug and slug not in slugs:
            slugs.append(slug)
    return slugs


def map_brand(raw):
    if pd.isna(raw) or not str(raw).strip():
        return ""
    s = to_slug(str(raw).strip())
    aliases = {
        "impelemtos-lopez": "implementos-lopez",
        "implementos-lopez": "implementos-lopez",
        "super-cria": "super-cria",
    }
    return aliases.get(s, s)


def normalize_unit(raw):
    if pd.isna(raw) or not str(raw).strip():
        return ""
    u = str(raw).strip().lower()
    unit_map = {
        "kilogramos": "kg",
        "kilogramo": "kg",
        "kg": "kg",
        "gramos": "g",
        "gramo": "g",
        "g": "g",
        "mililitros": "ml",
        "mililitro": "ml",
        "ml": "ml",
        "miligramos": "mg",
        "miligramo": "mg",
        "mg": "mg",
        "tabletas": "tabletas",
        "tableta": "tabletas",
        "litros": "l",
        "litro": "l",
        "l": "l",
    }
    return unit_map.get(u, to_slug(u))


def clean_val(v):
    if pd.isna(v):
        return None
    if isinstance(v, (np.bool_, bool)):
        return bool(v)
    if isinstance(v, (np.integer, int)):
        return int(v)
    if isinstance(v, (np.floating, float)):
        return float(v)
    s = str(v).strip()
    return s if s != "" else None


def main():
    med = pd.read_csv("medicamentos_veterinarios_rows.csv")
    masc = pd.read_csv("mascotas_rows.csv")
    alim_masc = pd.read_csv("alimentos_mascotas_rows.csv")
    acc_masc = pd.read_csv("accesorios_mascotas_rows.csv")
    alim_bal = pd.read_csv("alimentos_balanceados_rows.csv")
    impl = pd.read_csv("implementos_rows.csv")

    records = []

    for _, r in med.iterrows():
        attrs = {
            k: v
            for k, v in {
                "tipo": clean_val(r.get("tipo")),
                "edad": clean_val(r.get("edad")),
                "via_administracion": clean_val(r.get("via_administracion")),
                "presentacion": clean_val(r.get("presentacion")),
                "legacy_id": clean_val(r.get("id")),
                "origen_csv": "medicamentos_veterinarios_rows.csv",
                "url_imagen_anterior": clean_val(r.get("url")),
            }.items()
            if v is not None
        }
        records.append({
            "sku": "",
            "nombre": str(r["nombre"]).strip(),
            "descripcion": clean_val(r.get("informacion_adicional")) or "",
            "marca": map_brand(r.get("marca")),
            "categoria": "medicamentos-veterinarios",
            "especies": "|".join(map_species(r.get("especie"))),
            "contenido_valor": clean_val(r.get("contenido_decimal")) or "",
            "contenido_unidad": normalize_unit(r.get("contenido_medida")),
            "atributos_json": json.dumps(attrs, ensure_ascii=False),
            "activo": "true",
            "publicado": "true",
        })

    for _, r in alim_bal.iterrows():
        es_prod = bool(r.get("alimento_produccion")) if pd.notna(r.get("alimento_produccion")) else False
        cat_slug = "alimentos-para-produccion" if es_prod else "alimentos-balanceados"
        attrs = {
            k: v
            for k, v in {
                "alimento_produccion": es_prod,
                "materias_primas": clean_val(r.get("materias_primas")),
                "legacy_id": clean_val(r.get("id")),
                "origen_csv": "alimentos_balanceados_rows.csv",
                "url_imagen_anterior": clean_val(r.get("url")),
            }.items()
            if v is not None
        }
        records.append({
            "sku": "",
            "nombre": str(r["nombre"]).strip(),
            "descripcion": clean_val(r.get("informacion_adicional")) or "",
            "marca": map_brand(r.get("marca")),
            "categoria": cat_slug,
            "especies": "|".join(map_species(r.get("especie"))),
            "contenido_valor": clean_val(r.get("contenido_decimal")) or "",
            "contenido_unidad": normalize_unit(r.get("contenido_medida")),
            "atributos_json": json.dumps(attrs, ensure_ascii=False),
            "activo": "true",
            "publicado": "true",
        })

    masc_full = (
        masc.merge(alim_masc, on="id", how="left", suffixes=("", "_alim"))
        .merge(acc_masc, on="id", how="left", suffixes=("", "_acc"))
    )
    for _, r in masc_full.iterrows():
        sub = str(r.get("sub_categoria") or "").strip().lower()
        if "accesorio" in sub:
            cat_slug = "accesorios-para-mascotas"
            raw_sp = r.get("tipo_animal")
            c_val, c_unit, brand_raw = "", "", None
            attrs = {
                k: v
                for k, v in {
                    "sub_categoria": clean_val(r.get("sub_categoria")),
                    "que_es": clean_val(r.get("que_es")),
                    "recomendaciones_uso": clean_val(r.get("recomendaciones_uso")),
                    "legacy_id": clean_val(r.get("id")),
                    "origen_csv": "mascotas_rows.csv + accesorios_mascotas_rows.csv",
                    "url_imagen_anterior": clean_val(r.get("url")),
                }.items()
                if v is not None
            }
        else:
            cat_slug = "alimento-para-mascotas"
            raw_sp = r.get("especie_mascota")
            c_val = clean_val(r.get("contenido_decimal")) or ""
            c_unit = normalize_unit(r.get("contenido_medida"))
            brand_raw = r.get("marca")
            attrs = {
                k: v
                for k, v in {
                    "sub_categoria": clean_val(r.get("sub_categoria")),
                    "etapa_vida": clean_val(r.get("etapa_vida")),
                    "tamano_raza": clean_val(r.get("tamano_raza")),
                    "presentacion": clean_val(r.get("presentacion")),
                    "ingredientes_composicion_nutrimental": clean_val(
                        r.get("ingredientes_composicion_nutrimental")
                    ),
                    "legacy_id": clean_val(r.get("id")),
                    "origen_csv": "mascotas_rows.csv + alimentos_mascotas_rows.csv",
                    "url_imagen_anterior": clean_val(r.get("url")),
                }.items()
                if v is not None
            }

        records.append({
            "sku": "",
            "nombre": str(r["nombre"]).strip(),
            "descripcion": clean_val(r.get("informacion_adicional")) or "",
            "marca": map_brand(brand_raw),
            "categoria": cat_slug,
            "especies": "|".join(map_species(raw_sp)),
            "contenido_valor": c_val,
            "contenido_unidad": c_unit,
            "atributos_json": json.dumps(attrs, ensure_ascii=False),
            "activo": "true",
            "publicado": "true",
        })

    for _, r in impl.iterrows():
        que_es = str(r.get("que_es") or "").strip().lower()
        if any(k in que_es for k in ["comedero", "bebedero", "mamila", "biberon"]):
            cat_slug = "comederos-bebederos-y-mamilas"
        elif any(k in que_es for k in ["jaula", "voladero", "corral"]):
            cat_slug = "jaulas-voladeros-y-corrales"
        else:
            cat_slug = "herramientas-y-equipo"

        desc_parts = [
            p
            for p in [clean_val(r.get("recomendaciones_uso")), clean_val(r.get("informacion_adicional"))]
            if p
        ]
        attrs = {
            k: v
            for k, v in {
                "que_es": clean_val(r.get("que_es")),
                "tipo_animal_raw": clean_val(r.get("tipo_animal")),
                "presentaciones_disponibles": clean_val(r.get("presentaciones_disponibles")),
                "animales_especiales": clean_val(r.get("animales_especiales")),
                "legacy_id": clean_val(r.get("id")),
                "origen_csv": "implementos_rows.csv",
                "url_imagen_anterior": clean_val(r.get("url")),
            }.items()
            if v is not None
        }
        records.append({
            "sku": "",
            "nombre": str(r["nombre"]).strip(),
            "descripcion": "\n\n".join(desc_parts),
            "marca": map_brand(r.get("marca_distribuidor")),
            "categoria": cat_slug,
            "especies": "|".join(map_species(r.get("tipo_animal"))),
            "contenido_valor": "",
            "contenido_unidad": "",
            "atributos_json": json.dumps(attrs, ensure_ascii=False),
            "activo": "true",
            "publicado": "true",
        })

    out_df = pd.DataFrame(records)
    slug_counts = {}
    final_names = []
    for idx, row in out_df.iterrows():
        key = f"{to_slug(row['nombre'])}::{to_slug(row['contenido_unidad'])}"
        count = slug_counts.get(key, 0) + 1
        slug_counts[key] = count
        if count > 1:
            legacy_id = json.loads(row["atributos_json"]).get("legacy_id", idx + 1)
            final_names.append(f"{row['nombre']} (id {legacy_id})")
        else:
            final_names.append(row["nombre"])

    out_df["nombre"] = final_names
    out_df.to_csv("catalogo_maestro_limpio.csv", index=False, encoding="utf-8")
    print(f"Generado catalogo_maestro_limpio.csv con {len(out_df)} registros.")


if __name__ == "__main__":
    main()