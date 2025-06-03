
const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
const guidCharacters = '0123456789abcdef';

export function generateString(length: number): string {
    let result: string = '';

    for (let i = 0; i < length; i++) {
        result += characters.charAt(Math.floor(Math.random() * characters.length));
    }

    return result;
}

export function generateGuid(): string {
    let guidParts: string[] = ['', '', '', '', ''];

    for (let i = 0; i < 8; i++) {
        guidParts[0] += guidCharacters.charAt(Math.floor(Math.random() * guidCharacters.length));
    }

    for (let part = 1; part < 4; part++) {
        for (let i = 0; i < 4; i++) {
            guidParts[part] += guidCharacters.charAt(Math.floor(Math.random() * guidCharacters.length));
        }
    }

    for (let i = 0; i < 12; i++) {
        guidParts[4] += guidCharacters.charAt(Math.floor(Math.random() * guidCharacters.length));
    }

    return guidParts.join('-');
}