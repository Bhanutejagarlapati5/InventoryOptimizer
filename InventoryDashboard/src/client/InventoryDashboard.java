package client;

import javax.swing.*;
import java.awt.*;
import java.io.File;
import org.json.*;
import org.jfree.chart.ChartFactory;
import org.jfree.chart.ChartPanel;
import org.jfree.chart.JFreeChart;
import org.jfree.chart.plot.PlotOrientation;
import org.jfree.data.category.DefaultCategoryDataset;

public class InventoryDashboard {

    private JFrame frame;
    private JTextField salesInput;
    private JTextArea resultArea;
    private String currentUser = null;

    // Loading dialog
    private JDialog loadingDialog;

    public InventoryDashboard() {
        performLogin();

        frame = new JFrame("Inventory Forecast & Anomaly Detection - Logged in as: " + currentUser);
        frame.setSize(800, 600);
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);

        JLabel inputLabel = new JLabel("Enter sales (comma-separated):");
        salesInput = new JTextField(30);
        JButton forecastButton = new JButton("Get Forecast");
        JButton anomalyButton = new JButton("Detect Anomalies");
        JButton csvForecastButton = new JButton("Use CSV Forecast");
        JButton csvAnomalyButton = new JButton("Upload CSV for Anomalies");
        JButton swaggerButton = new JButton("Open API Docs");
        JButton logoutButton = new JButton("Logout");

        resultArea = new JTextArea(20, 65);
        resultArea.setLineWrap(true);
        resultArea.setWrapStyleWord(true);
        resultArea.setEditable(false);

        // Use async handlers to keep UI responsive
        forecastButton.addActionListener(e -> handleForecastAsync());
        anomalyButton.addActionListener(e -> handleAnomalyAsync());
        csvForecastButton.addActionListener(e -> handleCSVForecastAsync());
        csvAnomalyButton.addActionListener(e -> handleCSVAnomalyAsync());
        swaggerButton.addActionListener(e -> openSwaggerDocs());
        logoutButton.addActionListener(e -> handleLogout());

        JPanel panel = new JPanel();
        panel.setLayout(new FlowLayout());
        panel.add(inputLabel);
        panel.add(salesInput);
        panel.add(forecastButton);
        panel.add(anomalyButton);
        panel.add(csvForecastButton);
        panel.add(csvAnomalyButton);
        panel.add(swaggerButton);
        panel.add(logoutButton);
        panel.add(new JScrollPane(resultArea));

        frame.add(panel);
        frame.setVisible(true);
    }

    /* ======================
       Loading dialog helpers
       ====================== */
    private void showLoading(String msg) {
        if (loadingDialog != null && loadingDialog.isShowing()) return;

        JProgressBar bar = new JProgressBar();
        bar.setIndeterminate(true);

        JPanel p = new JPanel(new BorderLayout(10, 10));
        p.add(new JLabel(msg), BorderLayout.NORTH);
        p.add(bar, BorderLayout.CENTER);
        p.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));

        loadingDialog = new JDialog(frame, "Please wait…", true);
        loadingDialog.setDefaultCloseOperation(JDialog.DO_NOTHING_ON_CLOSE);
        loadingDialog.setContentPane(p);
        loadingDialog.pack();
        loadingDialog.setLocationRelativeTo(frame);

        SwingUtilities.invokeLater(() -> loadingDialog.setVisible(true));
    }

    private void hideLoading() {
        if (loadingDialog != null) {
            loadingDialog.setVisible(false);
            loadingDialog.dispose();
            loadingDialog = null;
        }
    }

    /* ======================
       Auth
       ====================== */
    private void performLogin() {
        while (true) {
            JPanel loginPanel = new JPanel(new GridLayout(2, 2));
            JTextField usernameField = new JTextField();
            JPasswordField passwordField = new JPasswordField();

            loginPanel.add(new JLabel("Username:"));
            loginPanel.add(usernameField);
            loginPanel.add(new JLabel("Password:"));
            loginPanel.add(passwordField);

            int option = JOptionPane.showConfirmDialog(null, loginPanel, "Login", JOptionPane.OK_CANCEL_OPTION);
            if (option != JOptionPane.OK_OPTION) {
                System.exit(0);
            }

            try {
                boolean success = ApiClient.login(usernameField.getText(), new String(passwordField.getPassword()));
                if (success) {
                    currentUser = usernameField.getText();
                    break;
                } else {
                    JOptionPane.showMessageDialog(null, "Invalid credentials. Try again.", "Login Failed", JOptionPane.ERROR_MESSAGE);
                }
            } catch (Exception e) {
                JOptionPane.showMessageDialog(null, "Login error: " + e.getMessage(), "Login Error", JOptionPane.ERROR_MESSAGE);
            }
        }
    }

    private void handleLogout() {
        showLoading("Logging out…");
        new SwingWorker<Void, Void>() {
            Exception error;

            @Override protected Void doInBackground() {
                try {
                    ApiClient.logout();
                } catch (Exception e) {
                    error = e;
                }
                return null;
            }
            @Override protected void done() {
                hideLoading();
                if (error != null) {
                    JOptionPane.showMessageDialog(frame, "Logout error: " + error.getMessage(), "Logout Error", JOptionPane.ERROR_MESSAGE);
                    return;
                }
                JOptionPane.showMessageDialog(frame, "Logged out successfully.", "Logout", JOptionPane.INFORMATION_MESSAGE);
                frame.dispose();
                new InventoryDashboard(); // Restart login flow
            }
        }.execute();
    }

    /* ======================
       Async handlers (SwingWorker)
       ====================== */
    private void handleForecastAsync() {
        int[] sales;
        try {
            sales = parseSales();
        } catch (Exception ex) {
            JOptionPane.showMessageDialog(frame, "Invalid input. Use comma-separated numbers.", "Input Error", JOptionPane.ERROR_MESSAGE);
            return;
        }

        showLoading("Getting forecast…");
        new SwingWorker<Void, Void>() {
            JSONObject response;
            Exception error;

            @Override protected Void doInBackground() {
                try {
                    response = ApiClient.getForecastWithMetrics(sales);
                } catch (Exception e) {
                    error = e;
                }
                return null;
            }
            @Override protected void done() {
                hideLoading();
                if (error != null) {
                    JOptionPane.showMessageDialog(frame, error.getMessage(), "Forecast Error", JOptionPane.ERROR_MESSAGE);
                    return;
                }
                try {
                    JSONArray forecastArray = response.getJSONArray("forecast");
                    JSONObject metrics = response.getJSONObject("metrics");

                    double[] forecast = new double[forecastArray.length()];
                    for (int i = 0; i < forecast.length; i++) {
                        forecast[i] = forecastArray.getDouble(i);
                    }

                    resultArea.setText("📊 Forecast:\n" + forecastArray.toString(2) +
                            "\n\n📈 Metrics:\nMAE: " + metrics.getDouble("mae") +
                            "\nRMSE: " + metrics.getDouble("rmse"));

                    showForecastChart(sales, forecast);
                } catch (Exception ex) {
                    JOptionPane.showMessageDialog(frame, ex.getMessage(), "Parse Error", JOptionPane.ERROR_MESSAGE);
                }
            }
        }.execute();
    }

    private void handleAnomalyAsync() {
        int[] sales;
        try {
            sales = parseSales();
        } catch (Exception ex) {
            JOptionPane.showMessageDialog(frame, "Invalid input. Use comma-separated numbers.", "Input Error", JOptionPane.ERROR_MESSAGE);
            return;
        }

        showLoading("Detecting anomalies…");
        new SwingWorker<Void, Void>() {
            JSONArray anomalies;
            Exception error;

            @Override protected Void doInBackground() {
                try {
                    anomalies = ApiClient.getAnomalies(sales);
                } catch (Exception e) {
                    error = e;
                }
                return null;
            }
            @Override protected void done() {
                hideLoading();
                if (error != null) {
                    JOptionPane.showMessageDialog(frame, error.getMessage(), "Anomaly Detection Error", JOptionPane.ERROR_MESSAGE);
                    return;
                }
                if (anomalies.length() == 0) {
                    resultArea.setText("✅ No anomalies detected.");
                    return;
                }

                StringBuilder result = new StringBuilder("⚠️ Anomalies Detected:\n");
                for (int i = 0; i < anomalies.length(); i++) {
                    JSONObject a = anomalies.getJSONObject(i);
                    result.append("🔸 Day ").append(a.getInt("day"))
                            .append(" → Value: ").append(a.getDouble("value"))
                            .append(", Z-Score: ").append(a.getDouble("z_score"))
                            .append(", Type: ").append(a.getString("type"))
                            .append("\n");
                }
                resultArea.setText(result.toString());
            }
        }.execute();
    }

    private void handleCSVForecastAsync() {
        showLoading("Forecasting from CSV…");
        new SwingWorker<Void, Void>() {
            JSONObject response;
            Exception error;

            @Override protected Void doInBackground() {
                try {
                    response = ApiClient.getForecastFromCSV();
                } catch (Exception e) {
                    error = e;
                }
                return null;
            }
            @Override protected void done() {
                hideLoading();
                if (error != null) {
                    JOptionPane.showMessageDialog(frame, error.getMessage(), "CSV Forecast Error", JOptionPane.ERROR_MESSAGE);
                    return;
                }
                try {
                    JSONArray forecastArray = response.getJSONArray("forecast");
                    resultArea.setText("📂 Forecast from CSV:\n" + forecastArray.toString(2));

                    double[] forecast = new double[forecastArray.length()];
                    for (int i = 0; i < forecast.length; i++) {
                        forecast[i] = forecastArray.getDouble(i);
                    }

                    // If you’ve got recent actuals, pass them here; for now zeroes.
                    int[] recentSales = new int[forecast.length];
                    for (int i = 0; i < recentSales.length; i++) recentSales[i] = 0;

                    showForecastChart(recentSales, forecast);
                } catch (Exception ex) {
                    JOptionPane.showMessageDialog(frame, ex.getMessage(), "Parse Error", JOptionPane.ERROR_MESSAGE);
                }
            }
        }.execute();
    }

    private void handleCSVAnomalyAsync() {
        JFileChooser fileChooser = new JFileChooser();
        int result = fileChooser.showOpenDialog(frame);
        if (result != JFileChooser.APPROVE_OPTION) return;

        File selectedFile = fileChooser.getSelectedFile();

        showLoading("Detecting anomalies from CSV…");
        new SwingWorker<Void, Void>() {
            JSONArray anomalies;
            Exception error;

            @Override protected Void doInBackground() {
                try {
                    anomalies = ApiClient.detectAnomalyFromCSV(selectedFile);
                } catch (Exception e) {
                    error = e;
                }
                return null;
            }
            @Override protected void done() {
                hideLoading();
                if (error != null) {
                    JOptionPane.showMessageDialog(frame, error.getMessage(), "CSV Anomaly Detection Error", JOptionPane.ERROR_MESSAGE);
                    return;
                }
                if (anomalies.length() == 0) {
                    resultArea.setText("✅ No anomalies detected from CSV.");
                    return;
                }

                StringBuilder output = new StringBuilder("📂 CSV Anomalies:\n");
                for (int i = 0; i < anomalies.length(); i++) {
                    JSONObject a = anomalies.getJSONObject(i);
                    output.append("🔸 Day ").append(a.getInt("day"))
                            .append(" → Value: ").append(a.getDouble("value"))
                            .append(", Z-Score: ").append(a.getDouble("z_score"))
                            .append(", Type: ").append(a.getString("type"))
                            .append("\n");
                }
                resultArea.setText(output.toString());
            }
        }.execute();
    }

    /* ======================
       Charts
       ====================== */
    private void showForecastChart(int[] actual, double[] forecast) {
        DefaultCategoryDataset dataset = new DefaultCategoryDataset();

        for (int i = 0; i < actual.length; i++) {
            dataset.addValue(actual[i], "Actual Sales", "Day " + (i + 1));
        }
        for (int i = 0; i < forecast.length; i++) {
            dataset.addValue(forecast[i], "Forecast", "Day " + (actual.length + i + 1));
        }

        JFreeChart lineChart = ChartFactory.createLineChart(
                "Sales Forecast",
                "Day",
                "Sales",
                dataset,
                PlotOrientation.VERTICAL,
                true, true, false);

        JFrame chartFrame = new JFrame("Forecast Chart");
        chartFrame.setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE);
        chartFrame.add(new ChartPanel(lineChart));
        chartFrame.setSize(800, 600);
        chartFrame.setVisible(true);
    }

    /* ======================
       Misc
       ====================== */
    private void openSwaggerDocs() {
        try {
            Desktop.getDesktop().browse(new java.net.URI("http://127.0.0.1:5000/docs"));
        } catch (Exception ex) {
            JOptionPane.showMessageDialog(frame, "Failed to open Swagger UI: " + ex.getMessage(), "Swagger Error", JOptionPane.ERROR_MESSAGE);
        }
    }

    private int[] parseSales() {
        String[] parts = salesInput.getText().split(",");
        int[] sales = new int[parts.length];
        for (int i = 0; i < parts.length; i++) {
            sales[i] = Integer.parseInt(parts[i].trim());
        }
        return sales;
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(InventoryDashboard::new);
    }
}
