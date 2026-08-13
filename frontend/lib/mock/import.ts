export type Column = {
  key: string;
  label: string;
};

export type Sheet = {
  id: string;
  name: string;
  description: string;
  columns: Column[];
  rows: (string | number)[][];
};
