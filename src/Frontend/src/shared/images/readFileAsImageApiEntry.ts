import type { ImageApiEntry } from "../../types/api";

function extractBase64FromDataUrl(dataUrl: string): string {
  const separatorIndex = dataUrl.indexOf(",");

  if (separatorIndex < 0) {
    throw new Error("Nie udało się odczytać danych obrazu w formacie data URL.");
  }

  return dataUrl.slice(separatorIndex + 1);
}

export async function readFileAsImageApiEntry(file: File): Promise<ImageApiEntry> {
  const dataUrl = await new Promise<string>((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = () => {
      if (typeof reader.result !== "string") {
        reject(new Error("Przeglądarka zwróciła nieobsługiwany wynik odczytu pliku."));
        return;
      }

      resolve(reader.result);
    };

    reader.onerror = () => {
      reject(new Error("Nie udało się odczytać wybranego pliku obrazu."));
    };

    reader.onabort = () => {
      reject(new Error("Odczyt wybranego pliku został przerwany."));
    };

    reader.readAsDataURL(file);
  });

  return {
    mimeType: file.type,
    base64: extractBase64FromDataUrl(dataUrl),
  };
}
