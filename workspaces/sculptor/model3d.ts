export interface Model3D { id: string; vertices: number; render(): string; }
export const cube: Model3D = { id: 'cube_01', vertices: 8, render() { return 'rendered'; } };