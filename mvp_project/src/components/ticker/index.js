import renderTicker from "./Ticker";
import api from "../../services/api";
import axios from "axios";

axios
    .get(api.news)
    .then((res) => renderTicker("ticker", res.data.reverse()))
    .then(() =>
        $(function() {
            $('[data-toggle="tooltip"]').tooltip();
        })
    );
