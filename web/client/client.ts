const selectState = document.getElementById('select-state') as HTMLSelectElement;
const progressBar = document.getElementById('progress-bar') as HTMLDivElement;
const progressPCT = document.getElementById('progress-pct') as HTMLSpanElement;
const nextHolidayContainer = document.getElementById('nx-holiday-container') as HTMLDivElement;
const nextName = document.getElementById('nx-name') as HTMLSpanElement;
const nextTimeDelta = document.getElementById('nx-time-delta') as HTMLSpanElement;
const nextDuration = document.getElementById('nx-duration') as HTMLSpanElement;

(window as any).dayjs.extend((window as any).dayjs_plugin_customParseFormat);

const STATES: string[] = [
    'Styria',
    'Carinthia',
    'Tirol',
    'Burgenland',
    'Salzburg',
    'Vorarlberg',
    'Upper Austria',
    'Lower Austria',
    'Vienna'
]

function transformState(state: string) {
    return state.replace(' ', '_').toLowerCase();
}


async function getPubIP(): Promise<string> {
    return fetch('https://api.ipify.org/?format=json')
        .then(async (res: Response) => {
            return (await res.json()).ip
        })

}

async function getCurrentSchoolYearDuration(state: string): Promise<{
    year: [number, number],
    duration: Record<string, any>
}> {
    const yearNow = dayjs().year() % 2000;
    const now = dayjs('20-04-2024', 'DD-MM-YYYY');
    console.log(now.toISOString());

    const requestYear = async (start: number, end: number) => {
        return await fetch(`/api/${start}/${end}/duration?state=${state}`)
            .then(async (res: Response) => {
                const jsonBody = (await res.json());
                console.log(jsonBody);
                if (!res.ok && ! jsonBody) {
                    throw new Error(`Backend-api returned: ${res.status}`);
                } else if (!jsonBody.success) {
                    throw new Error(`Backend-api returned: ${res.status}, Reason: ${jsonBody.reason}`);
                }

                return jsonBody.data;
            })
    }

    const yearOne: Record<string, any> = await requestYear(yearNow - 1, yearNow);

    console.log(now.isBefore(dayjs(yearOne['end'])));

    if (now.isBefore(dayjs(yearOne['end'])) && now.isAfter(dayjs(yearOne['start']))) {
        return {year: [yearNow - 1, yearNow], duration: yearOne};
    }

    return {year: [yearNow, yearNow + 1], duration: await requestYear(yearNow, yearNow + 1)}; // year two:
}

async function getState(ip: string): Promise<string> {
    return fetch(`http://ip-api.com/json/${ip}`) // sadly no https :(
        .then(async (res: Response) => {
            return (await res.json()).regionName
        })
}

async function init(selected: boolean = false) {
    const IP: string = await getPubIP();
    const state: string = !selected ? await getState(IP) : selectState.value;

    selectState.innerHTML = '';
    STATES.forEach((value, i) => {
        selectState.innerHTML += `
            <option value='${transformState(value)}' ${value == state && !selected ? ' selected' : ''}>${value + (value == state && !selected ? ' (Auto-detected)' : '')}</option>
        `
    });

    const yearResult = await getCurrentSchoolYearDuration(selectState.value);

    console.log(yearResult);

}

selectState.addEventListener('', async () => {
    await init(true);
})

init().then();