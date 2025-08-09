export interface APIList<T> {
    items: T[];
}


export function APIFiltersMap<T extends object>(filters: T): { [param: string]: string | number | boolean | ReadonlyArray<string | number | boolean> } {
    return Object.fromEntries(Object.entries(filters));
}