import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { TemplateEditor } from "@/app/(dashboard)/templates/_components/template-editor";
import { VersionHistory } from "@/app/(dashboard)/templates/_components/version-history";
import type { TemplateVersion, MergeTag } from "@/types/template";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }),
}));

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }));

vi.mock("@/lib/api/client", () => ({
  clientJson: vi.fn(),
}));

const mockMergeTags: MergeTag[] = [
  { tag: "{{first_name}}", label: "First name" },
  { tag: "{{email}}", label: "Email address" },
];

const mockVersion: TemplateVersion = {
  id: "tv-001",
  templateId: "tpl-001",
  version: 1,
  subject: "Hello {{first_name}}",
  bodyText: "Hi {{first_name}}, thanks for joining.",
  bodyHtml: "<p>Hi {{first_name}}, thanks for joining.</p>",
  publishedAt: "2026-01-10T10:00:00Z",
  createdAt: "2026-01-10T09:00:00Z",
};

const mockVersion2: TemplateVersion = {
  id: "tv-002",
  templateId: "tpl-001",
  version: 2,
  subject: "Quick check-in, {{first_name}}",
  bodyText: "Hi {{first_name}}, just checking in!",
  bodyHtml: "<p>Hi {{first_name}}, just checking in!</p>",
  publishedAt: "2026-03-15T14:00:00Z",
  createdAt: "2026-03-15T13:00:00Z",
};

const defaultEditorProps = {
  templateId: "tpl-001",
  initialVersion: mockVersion,
  mergeTags: mockMergeTags,
  isSaving: false,
  onSave: vi.fn(),
  onDraftChange: vi.fn(),
};

// ─── TemplateEditor ──────────────────────────────────────────────────────────

describe("TemplateEditor", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // localStorage is available in jsdom
    localStorage.clear();
  });

  it("renders subject, plain text, and HTML tabs", () => {
    render(<TemplateEditor {...defaultEditorProps} />);
    expect(screen.getByRole("tab", { name: "Subject" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Plain text" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "HTML" })).toBeInTheDocument();
  });

  it("shows subject input by default", () => {
    render(<TemplateEditor {...defaultEditorProps} />);
    expect(screen.getByLabelText("Subject line")).toBeInTheDocument();
  });

  it("populates subject from initialVersion", () => {
    render(<TemplateEditor {...defaultEditorProps} />);
    expect(screen.getByLabelText("Subject line")).toHaveValue(
      "Hello {{first_name}}",
    );
  });

  it("save button is disabled when no unsaved changes", () => {
    render(<TemplateEditor {...defaultEditorProps} />);
    expect(
      screen.getByRole("button", { name: /save as new version/i }),
    ).toBeDisabled();
  });

  it("save button is enabled after editing subject", () => {
    render(<TemplateEditor {...defaultEditorProps} />);
    const subjectInput = screen.getByLabelText("Subject line");
    fireEvent.change(subjectInput, { target: { value: "Updated subject" } });
    expect(
      screen.getByRole("button", { name: /save as new version/i }),
    ).not.toBeDisabled();
  });

  it("shows unsaved changes indicator after edit", () => {
    render(<TemplateEditor {...defaultEditorProps} />);
    fireEvent.change(screen.getByLabelText("Subject line"), {
      target: { value: "Changed" },
    });
    expect(screen.getByText(/unsaved changes/i)).toBeInTheDocument();
  });

  it("strips newlines from subject input", () => {
    render(<TemplateEditor {...defaultEditorProps} />);
    const input = screen.getByLabelText("Subject line");
    fireEvent.change(input, { target: { value: "line1\nline2" } });
    expect((input as HTMLInputElement).value).toBe("line1line2");
  });

  it("shows isSaving label on button when saving", () => {
    render(<TemplateEditor {...defaultEditorProps} isSaving={true} />);
    expect(
      screen.getByRole("button", { name: /saving/i }),
    ).toBeInTheDocument();
  });

  it("shows merge tag listbox when button is clicked", () => {
    render(<TemplateEditor {...defaultEditorProps} />);
    fireEvent.click(
      screen.getByRole("button", { name: /insert merge tag/i }),
    );
    expect(
      screen.getByRole("listbox", { name: /available merge tags/i }),
    ).toBeInTheDocument();
    expect(screen.getByText("First name")).toBeInTheDocument();
  });

  it("calls onDraftChange when subject changes", () => {
    const onDraftChange = vi.fn();
    render(
      <TemplateEditor {...defaultEditorProps} onDraftChange={onDraftChange} />,
    );
    fireEvent.change(screen.getByLabelText("Subject line"), {
      target: { value: "New subject" },
    });
    expect(onDraftChange).toHaveBeenCalledWith(
      expect.objectContaining({ subject: "New subject" }),
    );
  });

  it("switching to plain text tab shows textarea", () => {
    render(<TemplateEditor {...defaultEditorProps} />);
    fireEvent.click(screen.getByRole("tab", { name: "Plain text" }));
    expect(screen.getByLabelText("Plain-text body")).toBeInTheDocument();
  });
});

// ─── VersionHistory ──────────────────────────────────────────────────────────

describe("VersionHistory", () => {
  const versions = [mockVersion, mockVersion2];

  it("renders both versions", () => {
    render(
      <VersionHistory
        versions={versions}
        activeVersion={2}
        onRestore={vi.fn()}
        onSelect={vi.fn()}
        selectedVersion={mockVersion2}
      />,
    );
    expect(screen.getByText("v1")).toBeInTheDocument();
    expect(screen.getByText("v2")).toBeInTheDocument();
  });

  it("marks active version with Active badge", () => {
    render(
      <VersionHistory
        versions={versions}
        activeVersion={2}
        onRestore={vi.fn()}
        onSelect={vi.fn()}
        selectedVersion={mockVersion2}
      />,
    );
    expect(screen.getByText("Active")).toBeInTheDocument();
  });

  it("calls onSelect when View is clicked", () => {
    const onSelect = vi.fn();
    render(
      <VersionHistory
        versions={versions}
        activeVersion={2}
        onRestore={vi.fn()}
        onSelect={onSelect}
        selectedVersion={null}
      />,
    );
    const viewButtons = screen.getAllByRole("button", { name: "View" });
    fireEvent.click(viewButtons[0]!);
    expect(onSelect).toHaveBeenCalledOnce();
  });

  it("calls onRestore when Restore is clicked", () => {
    const onRestore = vi.fn();
    render(
      <VersionHistory
        versions={versions}
        activeVersion={2}
        onRestore={onRestore}
        onSelect={vi.fn()}
        selectedVersion={null}
      />,
    );
    const restoreButtons = screen.getAllByRole("button", { name: "Restore" });
    fireEvent.click(restoreButtons[0]!);
    expect(onRestore).toHaveBeenCalledOnce();
  });

  it("shows diff panel when Diff is clicked for two different versions", () => {
    render(
      <VersionHistory
        versions={versions}
        activeVersion={2}
        onRestore={vi.fn()}
        onSelect={vi.fn()}
        selectedVersion={mockVersion}
      />,
    );
    const diffButtons = screen.getAllByRole("button", { name: "Diff" });
    // Click diff on v2 (first in sorted order — newest first)
    fireEvent.click(diffButtons[0]!);
    expect(screen.getByLabelText("Version diff")).toBeInTheDocument();
  });
});
