import type { ReactNode } from "react";

type PropertiesListItem = {
  label: string;
  value: ReactNode;
};

type PropertiesListProps = {
  items: PropertiesListItem[];
};

export function PropertiesList({ items }: PropertiesListProps) {
  return (
    <div className="properties-list">
      {items.map((item) => (
        <div key={item.label} className="properties-row">
          <span className="properties-label">{item.label}</span>
          <span className="properties-value">{item.value}</span>
        </div>
      ))}
    </div>
  );
}
