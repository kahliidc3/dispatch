import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { UploadStep } from "@/app/(dashboard)/contacts/import/_components/upload-step";
import { MappingStep, buildInitialMapping } from "@/app/(dashboard)/contacts/import/_components/mapping-step";
import type { ColumnMapping } from "@/types/import";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }),
}));

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }));

vi.mock("@/lib/api/client", () => ({
  clientJson: vi.fn(),
}));

// ─── buildInitialMapping ─────────────────────────────────────────────────────

describe("buildInitialMapping", () => {
  it("auto-detects email column", () => {
    const mapping = buildInitialMapping(["email", "name"]);
    expect(mapping["email"]).toBe("email");
  });

  it("auto-detects first_name and last_name", () => {
    const mapping = buildInitialMapping(["first_name", "last_name"]);
    expect(mapping["first_name"]).toBe("first_name");
    expect(mapping["last_name"]).toBe("last_name");
  });

  it("case-insensitive match for Email", () => {
    const mapping = buildInitialMapping(["Email", "FirstName"]);
    expect(mapping["Email"]).toBe("email");
    expect(mapping["FirstName"]).toBe("first_name");
  });

  it("defaults unknown columns to skip", () => {
    const mapping = buildInitialMapping(["phone", "company"]);
    expect(mapping["phone"]).toBe("skip");
    expect(mapping["company"]).toBe("skip");
  });

  it("auto-detects newsletter preference column", () => {
    const mapping = buildInitialMapping(["newsletter"]);
    expect(mapping["newsletter"]).toBe("pref:newsletter");
  });
});

// ─── UploadStep ──────────────────────────────────────────────────────────────

describe("UploadStep", () => {
  it("renders the drop zone", () => {
    render(<UploadStep onParsed={vi.fn()} />);
    expect(screen.getByRole("button", { name: /drop zone/i })).toBeInTheDocument();
  });

  it("shows size limit hint", () => {
    render(<UploadStep onParsed={vi.fn()} />);
    expect(screen.getByText(/25 MB/)).toBeInTheDocument();
  });

  it("shows error when non-csv file is dropped", async () => {
    render(<UploadStep onParsed={vi.fn()} />);
    const file = new File(["hello"], "data.xlsx", {
      type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    });
    const dropZone = screen.getByRole("button", { name: /drop zone/i });
    fireEvent.drop(dropZone, { dataTransfer: { files: [file] } });
    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(/only .csv files/i),
    );
  });

  it("shows error when file is too large", async () => {
    render(<UploadStep onParsed={vi.fn()} />);
    const bigContent = "a".repeat(26 * 1024 * 1024);
    const file = new File([bigContent], "big.csv", { type: "text/csv" });
    const dropZone = screen.getByRole("button", { name: /drop zone/i });
    fireEvent.drop(dropZone, { dataTransfer: { files: [file] } });
    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(/25 MB/),
    );
  });
});

// ─── MappingStep ─────────────────────────────────────────────────────────────

const sampleHeaders = ["email", "first_name", "phone", "company"];
const sampleMapping: ColumnMapping = buildInitialMapping(sampleHeaders);

describe("MappingStep", () => {
  it("renders a select for each CSV column", () => {
    render(
      <MappingStep
        headers={sampleHeaders}
        initialMapping={sampleMapping}
        onBack={vi.fn()}
        onSubmit={vi.fn()}
        isSubmitting={false}
      />,
    );
    for (const header of sampleHeaders) {
      expect(
        screen.getByRole("combobox", { name: `Map column "${header}"` }),
      ).toBeInTheDocument();
    }
  });

  it("submit button is enabled when email is mapped", () => {
    render(
      <MappingStep
        headers={sampleHeaders}
        initialMapping={sampleMapping}
        onBack={vi.fn()}
        onSubmit={vi.fn()}
        isSubmitting={false}
      />,
    );
    expect(
      screen.getByRole("button", { name: /upload and start import/i }),
    ).not.toBeDisabled();
  });

  it("submit button is disabled when email is not mapped", () => {
    const noEmailMapping: ColumnMapping = { phone: "skip", company: "skip" };
    render(
      <MappingStep
        headers={["phone", "company"]}
        initialMapping={noEmailMapping}
        onBack={vi.fn()}
        onSubmit={vi.fn()}
        isSubmitting={false}
      />,
    );
    expect(
      screen.getByRole("button", { name: /upload and start import/i }),
    ).toBeDisabled();
  });

  it("shows in-progress label while submitting", () => {
    render(
      <MappingStep
        headers={sampleHeaders}
        initialMapping={sampleMapping}
        onBack={vi.fn()}
        onSubmit={vi.fn()}
        isSubmitting={true}
      />,
    );
    expect(
      screen.getByRole("button", { name: /uploading/i }),
    ).toBeInTheDocument();
  });

  it("calls onBack when back button is clicked", () => {
    const onBack = vi.fn();
    render(
      <MappingStep
        headers={sampleHeaders}
        initialMapping={sampleMapping}
        onBack={onBack}
        onSubmit={vi.fn()}
        isSubmitting={false}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /back/i }));
    expect(onBack).toHaveBeenCalledOnce();
  });

  it("clears duplicate singleton mappings (email can only be mapped once)", () => {
    render(
      <MappingStep
        headers={["col_a", "col_b"]}
        initialMapping={{ col_a: "email", col_b: "skip" }}
        onBack={vi.fn()}
        onSubmit={vi.fn()}
        isSubmitting={false}
      />,
    );
    const colBSelect = screen.getByRole("combobox", {
      name: 'Map column "col_b"',
    });
    fireEvent.change(colBSelect, { target: { value: "email" } });
    const colASelect = screen.getByRole("combobox", {
      name: 'Map column "col_a"',
    });
    expect((colASelect as HTMLSelectElement).value).toBe("skip");
  });
});
