import { WIZARD_STEPS } from "@/types/campaign";

type WizardNavProps = {
  currentStep: number;
};

export function WizardNav({ currentStep }: WizardNavProps) {
  return (
    <nav aria-label="Campaign wizard steps">
      <ol className="flex flex-wrap items-center gap-2">
        {WIZARD_STEPS.map((label, i) => {
          const done = i < currentStep;
          const active = i === currentStep;
          return (
            <li key={label} className="flex items-center gap-2">
              {i > 0 ? (
                <span aria-hidden="true" className="text-text-muted">
                  /
                </span>
              ) : null}
              <span
                aria-current={active ? "step" : undefined}
                className={`text-sm font-medium ${
                  active
                    ? "text-foreground"
                    : done
                      ? "text-text-muted line-through"
                      : "text-text-muted"
                }`}
              >
                {i + 1}. {label}
              </span>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
