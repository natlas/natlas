export default function makeXhrCall<T>(url: string): Promise<T> {
	return fetch(url)
		.then(response => response.json() as Promise<T>);
}