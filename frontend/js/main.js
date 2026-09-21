import { registerRoute, startRouter } from "./router.js";
import { mountNav } from "./components/nav.js";

import * as dashboard from "./pages/dashboard.js";
import * as soil from "./pages/soil.js";
import * as disease from "./pages/disease.js";
import * as recommend from "./pages/recommend.js";
import * as market from "./pages/market.js";
import * as weather from "./pages/weather.js";
import * as assistant from "./pages/assistant.js";
import * as login from "./pages/login.js";
import * as register from "./pages/register.js";

registerRoute("/", dashboard.render);
registerRoute("/soil", soil.render);
registerRoute("/disease", disease.render);
registerRoute("/recommend", recommend.render);
registerRoute("/market", market.render);
registerRoute("/weather", weather.render);
registerRoute("/assistant", assistant.render);
registerRoute("/login", login.render);
registerRoute("/register", register.render);

mountNav();
startRouter(document.getElementById("main"));
