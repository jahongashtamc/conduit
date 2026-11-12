export interface Model3D {
    id: string;
    vertices: number;
    render(): string;
}
export declare const cube: Model3D;
