export default function makeXhrCall<T>(url: string): Promise<T> {
    return fetch(url)
        .then((response) => response.json() as Promise<T>);
}

export function makeAuthXhrCall<T>(url: string): Promise<T> {
    return fetch(url, { credentials: 'same-origin', })
        .then((response) => response.json() as Promise<T>);
}
