package client;

import java.io.*;
import java.net.*;
import java.util.List;
import java.util.Map;
import org.json.*;

public class ApiClient {

    private static final String BASE_URL = "http://127.0.0.1:5000";
    private static String sessionCookie = "";

    // Login and store session cookie
    public static boolean login(String username, String password) throws Exception {
        URL url = new URL(BASE_URL + "/login");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("POST");
        conn.setRequestProperty("Content-Type", "application/json");
        conn.setDoOutput(true);

        JSONObject payload = new JSONObject();
        payload.put("username", username);
        payload.put("password", password);

        OutputStream os = conn.getOutputStream();
        os.write(payload.toString().getBytes());
        os.flush();

        int responseCode = conn.getResponseCode();
        if (responseCode == 200) {
            Map<String, List<String>> headerFields = conn.getHeaderFields();
            List<String> cookies = headerFields.get("Set-Cookie");
            if (cookies != null && !cookies.isEmpty()) {
                sessionCookie = cookies.get(0).split(";", 2)[0]; // JSESSIONID=...
            }
            return true;
        }
        return false;
    }

    public static JSONObject getForecastWithMetrics(int[] sales) throws Exception {
        URL url = new URL(BASE_URL + "/predict");
        HttpURLConnection conn = createConnectionWithSession(url, "POST", "application/json");

        JSONObject payload = new JSONObject();
        JSONArray salesArray = new JSONArray();
        for (int s : sales) salesArray.put(s);
        payload.put("sales", salesArray);

        OutputStream os = conn.getOutputStream();
        os.write(payload.toString().getBytes());
        os.flush();

        return readJsonResponse(conn);
    }

    public static JSONObject getForecastFromCSV() throws Exception {
        URL url = new URL(BASE_URL + "/predict_from_csv");
        HttpURLConnection conn = createConnectionWithSession(url, "GET", "application/json");
        return readJsonResponse(conn);
    }

    public static JSONArray getAnomalies(int[] sales) throws Exception {
        URL url = new URL(BASE_URL + "/detect_anomaly");
        HttpURLConnection conn = createConnectionWithSession(url, "POST", "application/json");

        JSONObject payload = new JSONObject();
        JSONArray salesArray = new JSONArray();
        for (int s : sales) salesArray.put(s);
        payload.put("sales", salesArray);

        OutputStream os = conn.getOutputStream();
        os.write(payload.toString().getBytes());
        os.flush();

        JSONObject response = readJsonResponse(conn);
        return response.getJSONArray("anomalies");
    }

    public static JSONArray detectAnomalyFromCSV(File csvFile) throws Exception {
        String boundary = Long.toHexString(System.currentTimeMillis());
        URL url = new URL(BASE_URL + "/detect_anomaly_csv");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setDoOutput(true);
        conn.setRequestMethod("POST");
        conn.setRequestProperty("Content-Type", "multipart/form-data; boundary=" + boundary);
        if (!sessionCookie.isEmpty()) {
            conn.setRequestProperty("Cookie", sessionCookie);
        }

        OutputStream output = conn.getOutputStream();
        PrintWriter writer = new PrintWriter(new OutputStreamWriter(output, "UTF-8"), true);

        String fileName = csvFile.getName();
        writer.append("--").append(boundary).append("\r\n");
        writer.append("Content-Disposition: form-data; name=\"file\"; filename=\"").append(fileName).append("\"\r\n");
        writer.append("Content-Type: text/csv\r\n\r\n").flush();

        FileInputStream inputStream = new FileInputStream(csvFile);
        byte[] buffer = new byte[4096];
        int bytesRead;
        while ((bytesRead = inputStream.read(buffer)) != -1) {
            output.write(buffer, 0, bytesRead);
        }
        output.flush();
        inputStream.close();
        writer.append("\r\n").flush();
        writer.append("--").append(boundary).append("--\r\n").flush();

        JSONObject response = readJsonResponse(conn);
        return response.getJSONArray("anomalies");
    }

    // Helpers

    private static HttpURLConnection createConnectionWithSession(URL url, String method, String contentType) throws Exception {
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod(method);
        conn.setRequestProperty("Content-Type", contentType);
        conn.setRequestProperty("Accept", "application/json");
        if (!sessionCookie.isEmpty()) {
            conn.setRequestProperty("Cookie", sessionCookie);
        }
        if (method.equals("POST")) {
            conn.setDoOutput(true);
        }
        return conn;
    }

    private static JSONObject readJsonResponse(HttpURLConnection conn) throws Exception {
        BufferedReader br = new BufferedReader(new InputStreamReader(
                conn.getResponseCode() >= 400 ? conn.getErrorStream() : conn.getInputStream()));
        StringBuilder sb = new StringBuilder();
        String line;
        while ((line = br.readLine()) != null) sb.append(line);
        return new JSONObject(sb.toString());
    }
    public static void logout() throws Exception {
        URL url = new URL("http://127.0.0.1:5000/logout");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("GET");
        conn.setRequestProperty("Cookie", sessionCookie); // if session management is handled via cookie
        conn.getInputStream().close(); // Just trigger the endpoint
    }

}
